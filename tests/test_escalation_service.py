from app.domain.enums import DecisionType, IntentName
from app.domain.services.escalation_service import EscalationService
from app.domain.services.policy_service import PolicyService


class TestEscalationService:
    def setup_method(self) -> None:
        self.policy_svc = PolicyService()
        self.escalation_svc = EscalationService()

    def test_safe_continue(self) -> None:
        policy = self.policy_svc.check(IntentName.CHECK_ORDER_STATUS, 0.92, verified=True)
        decision = self.escalation_svc.decide(
            intent=IntentName.CHECK_ORDER_STATUS,
            confidence=0.92,
            policy_result=policy,
        )
        assert decision.decision == DecisionType.CONTINUE
        assert decision.reason == "safe_to_continue"

    def test_low_confidence_clarify(self) -> None:
        policy = self.policy_svc.check(IntentName.CHECK_ORDER_STATUS, 0.60, verified=True)
        decision = self.escalation_svc.decide(
            intent=IntentName.CHECK_ORDER_STATUS,
            confidence=0.60,
            policy_result=policy,
        )
        assert decision.decision == DecisionType.CLARIFY
        assert "low_confidence" in decision.reason

    def test_risky_action_without_verification(self) -> None:
        policy = self.policy_svc.check(IntentName.CANCEL_ORDER, 0.88, verified=False)
        decision = self.escalation_svc.decide(
            intent=IntentName.CANCEL_ORDER,
            confidence=0.88,
            policy_result=policy,
        )
        assert decision.decision == DecisionType.HANDOFF
        assert "missing_verification" in decision.reason

    def test_downstream_failure_handoff(self) -> None:
        policy = self.policy_svc.check(IntentName.CHECK_ORDER_STATUS, 0.92, verified=True)
        decision = self.escalation_svc.decide(
            intent=IntentName.CHECK_ORDER_STATUS,
            confidence=0.92,
            policy_result=policy,
            downstream_failed=True,
        )
        assert decision.decision == DecisionType.HANDOFF
        assert decision.reason == "downstream_api_failed"
        assert decision.risk_score == 1.0

    def test_very_low_confidence_handoff(self) -> None:
        policy = self.policy_svc.check(IntentName.UNKNOWN, 0.15, verified=False)
        decision = self.escalation_svc.decide(
            intent=IntentName.UNKNOWN,
            confidence=0.15,
            policy_result=policy,
        )
        assert decision.decision == DecisionType.HANDOFF
