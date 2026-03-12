from dataclasses import dataclass

from app.domain.enums import IntentName
from app.domain.rules.policy_rules import PolicyViolation, evaluate_policies


@dataclass(frozen=True, slots=True)
class PolicyResult:
    violations: list[PolicyViolation]
    risk_score: float
    has_denials: bool


class PolicyService:
    def check(
        self,
        intent: IntentName,
        confidence: float,
        verified: bool,
    ) -> PolicyResult:
        violations = evaluate_policies(intent, confidence, verified)

        risk_score = self._compute_risk_score(violations)
        has_denials = any(v.severity == "deny" for v in violations)

        return PolicyResult(
            violations=violations,
            risk_score=risk_score,
            has_denials=has_denials,
        )

    @staticmethod
    def _compute_risk_score(violations: list[PolicyViolation]) -> float:
        if not violations:
            return 0.0

        score = 0.0
        for v in violations:
            if v.severity == "deny":
                score += 0.5
            else:
                score += 0.2

        return min(score, 1.0)
