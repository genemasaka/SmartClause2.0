
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from subscription_manager import SubscriptionManager, PAY_AS_YOU_GO_TIER, STANDARD_TIER

class TestSubscriptionManager(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.manager = SubscriptionManager(self.mock_db)
        
    def test_get_user_status_no_subscription(self):
        # Setup: DB returns None
        self.mock_db.get_user_subscription.return_value = None
        
        status = self.manager.get_user_status("user_123")
        
        self.assertEqual(status["tier"], PAY_AS_YOU_GO_TIER)
        self.assertEqual(status["credits"], 0)
        self.assertTrue(status["is_active"]) # Always active for pay-as-you-go
        
    def test_get_user_status_pay_as_you_go(self):
        # Setup: DB returns valid pay-as-you-go sub
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": PAY_AS_YOU_GO_TIER,
            "credits_remaining": 5,
            "subscription_end_date": None
        }
        
        status = self.manager.get_user_status("user_123")
        
        self.assertEqual(status["tier"], PAY_AS_YOU_GO_TIER)
        self.assertEqual(status["credits"], 5)
        
    def test_get_user_status_standard_active(self):
        # Setup: DB returns active standard sub
        future_date = (datetime.now() + timedelta(days=10)).isoformat()
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": STANDARD_TIER,
            "credits_remaining": 0,
            "subscription_end_date": future_date
        }
        
        status = self.manager.get_user_status("user_123")
        
        self.assertEqual(status["tier"], STANDARD_TIER)
        self.assertTrue(status["is_active"])
        self.assertGreater(status["days_remaining"], 0)
        
    def test_get_user_status_standard_expired(self):
        # Setup: DB returns expired standard sub
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": STANDARD_TIER,
            "credits_remaining": 0,
            "subscription_end_date": past_date
        }
        
        status = self.manager.get_user_status("user_123")
        
        self.assertEqual(status["tier"], STANDARD_TIER)
        self.assertFalse(status["is_active"])
        self.assertEqual(status["days_remaining"], 0)

    def test_has_access_editor_standard(self):
        # Setup: Active Standard
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": STANDARD_TIER,
            "subscription_end_date": (datetime.now() + timedelta(days=10)).isoformat()
        }
        
        has_access = self.manager.has_access("user_123", "document_editor")
        self.assertTrue(has_access)
        
    def test_has_access_editor_payg(self):
        # Setup: Pay-as-you-go
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": PAY_AS_YOU_GO_TIER
        }
        
        has_access = self.manager.has_access("user_123", "document_editor")
        self.assertFalse(has_access)

    def test_can_generate_document_payg_with_credits(self):
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": PAY_AS_YOU_GO_TIER,
            "credits_remaining": 1
        }
        self.assertTrue(self.manager.can_generate_document("user_123"))
        
    def test_can_generate_document_payg_no_credits(self):
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": PAY_AS_YOU_GO_TIER,
            "credits_remaining": 0
        }
        self.assertFalse(self.manager.can_generate_document("user_123"))
        
    def test_deduct_credit_success(self):
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": PAY_AS_YOU_GO_TIER,
            "credits_remaining": 2
        }
        self.mock_db.update_subscription_credits.return_value = {"credits_remaining": 1}
        
        success = self.manager.deduct_credit("user_123", "doc_1")
        
        self.assertTrue(success)
        self.mock_db.update_subscription_credits.assert_called_with("user_123", -1)
        self.mock_db.log_document_generation.assert_called()

    def test_deduct_credit_standard_user(self):
        # Standard users shouldn't lose credits
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": STANDARD_TIER,
            "credits_remaining": 0,
            "subscription_end_date": (datetime.now() + timedelta(days=10)).isoformat()
        }
        
        success = self.manager.deduct_credit("user_123", "doc_1")
        
        self.assertTrue(success)
        self.mock_db.update_subscription_credits.assert_not_called()
        self.mock_db.log_document_generation.assert_called()

if __name__ == '__main__':
    unittest.main()
