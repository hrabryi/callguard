import re
from dataclasses import dataclass

from app.domain.enums import IntentName

_PATTERNS: list[tuple[re.Pattern[str], IntentName, float]] = [
    (re.compile(r"\b(cancel|refund)\b.*\b(order|purchase)\b", re.I), IntentName.CANCEL_ORDER, 0.88),
    (re.compile(r"\b(where|track|status)\b.*\b(order|package|delivery)\b", re.I), IntentName.CHECK_ORDER_STATUS, 0.92),
    (re.compile(r"\b(bill|charge|invoice|payment)\b", re.I), IntentName.BILLING_QUESTION, 0.80),
    (re.compile(r"\b(cancel)\b", re.I), IntentName.CANCEL_ORDER, 0.65),
    (re.compile(r"\b(order)\b", re.I), IntentName.CHECK_ORDER_STATUS, 0.55),
]


@dataclass(frozen=True, slots=True)
class IntentResult:
    intent: IntentName
    confidence: float
    extracted_entities: dict[str, str]


class IntentService:
    """Rule-based intent parser. In production this would call an LLM or NLU model."""

    def predict(self, text: str) -> IntentResult:
        text_lower = text.lower().strip()

        for pattern, intent, base_confidence in _PATTERNS:
            if pattern.search(text_lower):
                entities = self._extract_entities(text_lower, intent)
                return IntentResult(
                    intent=intent,
                    confidence=base_confidence,
                    extracted_entities=entities,
                )

        return IntentResult(
            intent=IntentName.UNKNOWN,
            confidence=0.15,
            extracted_entities={},
        )

    @staticmethod
    def _extract_entities(text: str, intent: IntentName) -> dict[str, str]:
        entities: dict[str, str] = {}

        order_match = re.search(r"#?(\d{4,})", text)
        if order_match:
            entities["order_id"] = order_match.group(1)

        if intent == IntentName.CANCEL_ORDER:
            reason_match = re.search(r"because\s+(.+?)(?:\.|$)", text)
            if reason_match:
                entities["reason"] = reason_match.group(1).strip()

        return entities
