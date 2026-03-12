import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.enums import CallStatus, DecisionType, EventType, ScenarioName
from app.domain.services.downstream_adapter import (
    DownstreamTimeoutError,
    OrderServiceAdapter,
)
from app.domain.services.escalation_service import EscalationDecision, EscalationService
from app.domain.services.handoff_service import HandoffService
from app.domain.services.intent_service import IntentResult, IntentService
from app.domain.services.policy_service import PolicyResult, PolicyService
from app.repositories.call_repository import CallRepository
from app.repositories.decision_repository import DecisionRepository
from app.repositories.event_repository import EventRepository
from app.schemas.calls import UtteranceResultResponse

logger = get_logger(__name__)

_SCENARIOS: dict[ScenarioName, dict] = {
    ScenarioName.SAFE_CONTINUE: {
        "phone": "+13105550001",
        "utterance": "Where is my order #12345?",
        "verified": True,
        "force_downstream_failure": False,
    },
    ScenarioName.LOW_CONFIDENCE_CLARIFY: {
        "phone": "+13105550002",
        "utterance": "Hmm, something about my thing",
        "verified": False,
        "force_downstream_failure": False,
    },
    ScenarioName.CANCEL_ORDER_UNVERIFIED: {
        "phone": "+13105550003",
        "utterance": "I want to cancel my order",
        "verified": False,
        "force_downstream_failure": False,
    },
    ScenarioName.DOWNSTREAM_FAILURE: {
        "phone": "+13105550004",
        "utterance": "Where is my order #99421?",
        "verified": True,
        "force_downstream_failure": True,
    },
}


class SimulationService:
    """Orchestrates the full utterance-processing pipeline and records events."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._call_repo = CallRepository(session)
        self._event_repo = EventRepository(session)
        self._decision_repo = DecisionRepository(session)
        self._intent_svc = IntentService()
        self._policy_svc = PolicyService()
        self._escalation_svc = EscalationService()
        self._handoff_svc = HandoffService()
        self._downstream = OrderServiceAdapter()

    async def create_call(self, caller_phone: str) -> int:
        external_id = f"call-{uuid.uuid4().hex[:12]}"
        call = await self._call_repo.create(external_id, caller_phone)
        logger.info("call_created", call_id=call.id, external_id=external_id)
        return call.id

    async def process_utterance(
        self,
        call_id: int,
        text: str,
        verified: bool = False,
        simulate_downstream_failure: bool = False,
    ) -> UtteranceResultResponse:
        # 1. Record utterance
        await self._event_repo.create(
            call_session_id=call_id,
            event_type=EventType.UTTERANCE_RECEIVED,
            payload={"text": text, "verified": verified},
        )

        # 2. Predict intent
        t0 = time.perf_counter()
        intent_result: IntentResult = self._intent_svc.predict(text)
        intent_latency = (time.perf_counter() - t0) * 1000

        await self._event_repo.create(
            call_session_id=call_id,
            event_type=EventType.INTENT_PREDICTED,
            payload={
                "intent": intent_result.intent.value,
                "confidence": intent_result.confidence,
                "entities": intent_result.extracted_entities,
            },
            latency_ms=round(intent_latency, 2),
        )

        # 3. Check policies
        t0 = time.perf_counter()
        policy_result: PolicyResult = self._policy_svc.check(
            intent_result.intent, intent_result.confidence, verified
        )
        policy_latency = (time.perf_counter() - t0) * 1000

        await self._event_repo.create(
            call_session_id=call_id,
            event_type=EventType.POLICY_CHECKED,
            payload={
                "violations": [
                    {"rule": v.rule, "severity": v.severity, "description": v.description}
                    for v in policy_result.violations
                ],
                "risk_score": policy_result.risk_score,
            },
            latency_ms=round(policy_latency, 2),
        )

        # 4. Optionally call downstream
        downstream_failed = False
        if not policy_result.has_denials:
            try:
                t0 = time.perf_counter()
                ds_result = await self._downstream.check_order_status(
                    order_id=intent_result.extracted_entities.get("order_id"),
                    force_failure=simulate_downstream_failure,
                )
                ds_latency = (time.perf_counter() - t0) * 1000

                await self._event_repo.create(
                    call_session_id=call_id,
                    event_type=EventType.DOWNSTREAM_CALLED,
                    payload={"success": True, "data": ds_result.data},
                    latency_ms=round(ds_latency, 2),
                )
            except DownstreamTimeoutError:
                ds_latency = (time.perf_counter() - t0) * 1000
                downstream_failed = True

                await self._event_repo.create(
                    call_session_id=call_id,
                    event_type=EventType.DOWNSTREAM_CALLED,
                    payload={"success": False, "error": "timeout"},
                    latency_ms=round(ds_latency, 2),
                )

        # 5. Escalation decision
        decision: EscalationDecision = self._escalation_svc.decide(
            intent=intent_result.intent.value,
            confidence=intent_result.confidence,
            policy_result=policy_result,
            downstream_failed=downstream_failed,
        )

        await self._event_repo.create(
            call_session_id=call_id,
            event_type=EventType.DECISION_MADE,
            payload={
                "decision": decision.decision.value,
                "reason": decision.reason,
                "risk_score": decision.risk_score,
            },
        )

        await self._decision_repo.create(
            call_session_id=call_id,
            intent=intent_result.intent.value,
            confidence=intent_result.confidence,
            risk_score=decision.risk_score,
            decision=decision.decision,
            reason=decision.reason,
        )

        # 6. Handoff summary if needed
        handoff_summary: str | None = None
        if decision.decision == DecisionType.HANDOFF:
            handoff_summary = self._handoff_svc.generate_summary(
                intent_result, decision, text
            )
            await self._decision_repo.create_handoff_summary(
                call_session_id=call_id,
                summary=handoff_summary,
                reason=decision.reason,
            )
            await self._event_repo.create(
                call_session_id=call_id,
                event_type=EventType.HANDOFF_CREATED,
                payload={"summary": handoff_summary},
            )
            await self._call_repo.update_status(call_id, CallStatus.HANDED_OFF)

        logger.info(
            "utterance_processed",
            call_id=call_id,
            intent=intent_result.intent.value,
            confidence=intent_result.confidence,
            decision=decision.decision.value,
        )

        return UtteranceResultResponse(
            intent=intent_result.intent.value,
            confidence=intent_result.confidence,
            risk_score=decision.risk_score,
            decision=decision.decision,
            reason=decision.reason,
            handoff_summary=handoff_summary,
        )

    async def run_scenario(self, scenario: ScenarioName) -> int:
        spec = _SCENARIOS[scenario]
        call_id = await self.create_call(spec["phone"])
        await self.process_utterance(
            call_id=call_id,
            text=spec["utterance"],
            verified=spec["verified"],
            simulate_downstream_failure=spec["force_downstream_failure"],
        )
        return call_id
