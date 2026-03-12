from dataclasses import dataclass

from app.domain.enums import DecisionType
from app.domain.services.policy_service import PolicyResult


@dataclass(frozen=True, slots=True)
class EscalationDecision:
    decision: DecisionType
    reason: str
    risk_score: float


class EscalationService:
    """Core decision engine. Takes intent + policy + downstream signals and produces a routing decision."""

    def decide(
        self,
        intent: str,
        confidence: float,
        policy_result: PolicyResult,
        downstream_failed: bool = False,
    ) -> EscalationDecision:
        if downstream_failed:
            return EscalationDecision(
                decision=DecisionType.HANDOFF,
                reason="downstream_api_failed",
                risk_score=1.0,
            )

        if policy_result.has_denials:
            denial_rules = [v.rule for v in policy_result.violations if v.severity == "deny"]
            return EscalationDecision(
                decision=DecisionType.HANDOFF,
                reason=f"policy_denied:{','.join(denial_rules)}",
                risk_score=policy_result.risk_score,
            )

        if confidence < 0.5:
            return EscalationDecision(
                decision=DecisionType.HANDOFF,
                reason="very_low_confidence",
                risk_score=max(policy_result.risk_score, 0.7),
            )

        if confidence < 0.75:
            return EscalationDecision(
                decision=DecisionType.CLARIFY,
                reason="low_confidence",
                risk_score=policy_result.risk_score,
            )

        return EscalationDecision(
            decision=DecisionType.CONTINUE,
            reason="safe_to_continue",
            risk_score=policy_result.risk_score,
        )
