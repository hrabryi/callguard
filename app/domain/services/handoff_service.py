from app.domain.services.escalation_service import EscalationDecision
from app.domain.services.intent_service import IntentResult

_REASON_TEMPLATES: dict[str, str] = {
    "downstream_api_failed": (
        "Caller requested '{intent}' but the downstream service is unavailable. "
        "Manual intervention required."
    ),
    "very_low_confidence": (
        "AI could not reliably determine caller intent (confidence: {confidence:.0%}). "
        "Please verify what the caller needs."
    ),
}


class HandoffService:
    def generate_summary(
        self,
        intent_result: IntentResult,
        decision: EscalationDecision,
        utterance: str,
    ) -> str:
        template = _REASON_TEMPLATES.get(decision.reason)
        if template:
            return template.format(
                intent=intent_result.intent.value,
                confidence=intent_result.confidence,
            )

        entities_str = ", ".join(
            f"{k}={v}" for k, v in intent_result.extracted_entities.items()
        )
        entity_info = f" Extracted entities: {entities_str}." if entities_str else ""

        return (
            f"Caller said: \"{utterance}\". "
            f"Detected intent: {intent_result.intent.value} "
            f"(confidence: {intent_result.confidence:.0%}). "
            f"Escalation reason: {decision.reason}.{entity_info}"
        )
