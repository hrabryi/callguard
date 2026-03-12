from enum import StrEnum


class CallStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    HANDED_OFF = "handed_off"
    FAILED = "failed"


class IntentName(StrEnum):
    CHECK_ORDER_STATUS = "check_order_status"
    CANCEL_ORDER = "cancel_order"
    BILLING_QUESTION = "billing_question"
    UNKNOWN = "unknown"


class DecisionType(StrEnum):
    CONTINUE = "continue"
    CLARIFY = "clarify"
    FALLBACK = "fallback"
    HANDOFF = "handoff"


class EventType(StrEnum):
    UTTERANCE_RECEIVED = "utterance_received"
    INTENT_PREDICTED = "intent_predicted"
    POLICY_CHECKED = "policy_checked"
    DECISION_MADE = "decision_made"
    HANDOFF_CREATED = "handoff_created"
    DOWNSTREAM_CALLED = "downstream_called"


class ScenarioName(StrEnum):
    SAFE_CONTINUE = "safe_continue"
    LOW_CONFIDENCE_CLARIFY = "low_confidence_clarify"
    CANCEL_ORDER_UNVERIFIED = "cancel_order_unverified"
    DOWNSTREAM_FAILURE = "downstream_failure"
