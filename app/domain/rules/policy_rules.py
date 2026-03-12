from dataclasses import dataclass

from app.domain.enums import IntentName

RISKY_INTENTS: frozenset[IntentName] = frozenset({
    IntentName.CANCEL_ORDER,
})

CONFIDENCE_THRESHOLD_DENY = 0.4
CONFIDENCE_THRESHOLD_WARN = 0.75


@dataclass(frozen=True, slots=True)
class PolicyViolation:
    rule: str
    severity: str  # "warn" | "deny"
    description: str


def evaluate_policies(
    intent: IntentName,
    confidence: float,
    verified: bool,
) -> list[PolicyViolation]:
    violations: list[PolicyViolation] = []

    if intent in RISKY_INTENTS and not verified:
        violations.append(
            PolicyViolation(
                rule="missing_verification",
                severity="deny",
                description=f"Intent '{intent}' requires identity verification",
            )
        )

    if confidence < CONFIDENCE_THRESHOLD_DENY:
        violations.append(
            PolicyViolation(
                rule="very_low_confidence",
                severity="deny",
                description=f"Confidence {confidence:.2f} is below minimum threshold {CONFIDENCE_THRESHOLD_DENY}",
            )
        )
    elif confidence < CONFIDENCE_THRESHOLD_WARN:
        violations.append(
            PolicyViolation(
                rule="low_confidence",
                severity="warn",
                description=f"Confidence {confidence:.2f} is below safe threshold {CONFIDENCE_THRESHOLD_WARN}",
            )
        )

    if intent == IntentName.BILLING_QUESTION and not verified:
        violations.append(
            PolicyViolation(
                rule="billing_unverified",
                severity="warn",
                description="Billing questions from unverified callers are flagged",
            )
        )

    return violations
