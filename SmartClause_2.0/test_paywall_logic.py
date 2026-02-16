
import unittest
from unittest.mock import MagicMock
from subscription_manager import SubscriptionManager, STANDARD_TIER, SINGLE_CREDIT_TIER, PAY_AS_YOU_GO_TIER

class TestSubscriptionManager(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.sub_manager = SubscriptionManager(self.mock_db)
        self.user_id = "test_user_123"

    def test_can_generate_document_standard(self):
        # Setup Standard user
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": STANDARD_TIER,
            "subscription_end_date": "2030-01-01T00:00:00.000000+00:00",
            "credits_remaining": 0
        }
        
        can_generate = self.sub_manager.can_generate_document(self.user_id)
        self.assertTrue(can_generate, "Standard user should be able to generate")

    def test_can_generate_document_single_credit_with_credits(self):
        # Setup Single Credit user with credits
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": SINGLE_CREDIT_TIER,
            "credits_remaining": 1
        }
        
        can_generate = self.sub_manager.can_generate_document(self.user_id)
        self.assertTrue(can_generate, "User with credits should be able to generate")

    def test_can_generate_document_single_credit_no_credits(self):
        # Setup Single Credit user without credits
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": SINGLE_CREDIT_TIER,
            "credits_remaining": 0
        }
        
        can_generate = self.sub_manager.can_generate_document(self.user_id)
        self.assertFalse(can_generate, "User without credits should NOT be able to generate")

    def test_deduct_credit_standard(self):
        # Standard user - no deduction
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": STANDARD_TIER,
             "subscription_end_date": "2030-01-01T00:00:00.000000+00:00"
        }
        
        success = self.sub_manager.deduct_credit(self.user_id, "doc_1")
        self.assertTrue(success)
        self.mock_db.update_subscription_credits.assert_not_called()
        self.mock_db.log_document_generation.assert_called_with(self.user_id, "doc_1", 0, STANDARD_TIER)

    def test_deduct_credit_payg(self):
        # PAYG user - explicit deduction
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": PAY_AS_YOU_GO_TIER,
            "credits_remaining": 5
        }
        self.mock_db.update_subscription_credits.return_value = {"credits_remaining": 4}
        
        success = self.sub_manager.deduct_credit(self.user_id, "doc_1")
        self.assertTrue(success)
        self.mock_db.update_subscription_credits.assert_called_with(self.user_id, -1)
        self.mock_db.log_document_generation.assert_called_with(self.user_id, "doc_1", 1, PAY_AS_YOU_GO_TIER)

    def test_deduct_credit_fail_no_credits(self):
        # PAYG user - 0 credits
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": PAY_AS_YOU_GO_TIER,
            "credits_remaining": 0
        }
        
        success = self.sub_manager.deduct_credit(self.user_id, "doc_1")
        self.assertFalse(success)
        self.mock_db.update_subscription_credits.assert_not_called()

    def test_feature_access(self):
        # Standard User
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": STANDARD_TIER,
            "subscription_end_date": "2030-01-01T00:00:00.000000+00:00"
        }
        self.assertTrue(self.sub_manager.has_access(self.user_id, "document_editor"))
        self.assertTrue(self.sub_manager.has_access(self.user_id, "clause_library"))

        # PAYG User
        self.mock_db.get_user_subscription.return_value = {
            "subscription_tier": PAY_AS_YOU_GO_TIER,
            "credits_remaining": 10
        }
        self.assertFalse(self.sub_manager.has_access(self.user_id, "document_editor"))
        self.assertFalse(self.sub_manager.has_access(self.user_id, "clause_library"))

if __name__ == '__main__':
    unittest.main()
