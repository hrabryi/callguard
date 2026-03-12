from app.domain.enums import IntentName
from app.domain.services.policy_service import PolicyService


class TestPolicyService:
    def setup_method(self) -> None:
        self.svc = PolicyService()

    def test_safe_intent_no_violations(self) -> None:
        result = self.svc.check(IntentName.CHECK_ORDER_STATUS, 0.92, verified=True)
        assert result.violations == []
        assert result.risk_score == 0.0
        assert result.has_denials is False

    def test_cancel_order_unverified_denied(self) -> None:
        result = self.svc.check(IntentName.CANCEL_ORDER, 0.88, verified=False)
        assert result.has_denials is True
        rules = [v.rule for v in result.violations]
        assert "missing_verification" in rules

    def test_low_confidence_warning(self) -> None:
        result = self.svc.check(IntentName.CHECK_ORDER_STATUS, 0.60, verified=True)
        assert result.has_denials is False
        rules = [v.rule for v in result.violations]
        assert "low_confidence" in rules

    def test_very_low_confidence_denied(self) -> None:
        result = self.svc.check(IntentName.UNKNOWN, 0.2, verified=False)
        assert result.has_denials is True
        rules = [v.rule for v in result.violations]
        assert "very_low_confidence" in rules

    def test_billing_unverified_warning(self) -> None:
        result = self.svc.check(IntentName.BILLING_QUESTION, 0.80, verified=False)
        rules = [v.rule for v in result.violations]
        assert "billing_unverified" in rules
