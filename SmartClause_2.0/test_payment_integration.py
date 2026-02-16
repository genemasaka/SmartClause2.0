"""
Test script for Phase 3 Payment Integration
Verifies organization subscription payment flow and metadata storage
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from payment_flow import PaymentFlowManager
from database import DatabaseManager
from subscription_manager import INDIVIDUAL_TIER, TEAM_TIER, PRICING

class TestPaymentIntegration(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.mock_mpesa = MagicMock()
        self.payment_manager = PaymentFlowManager(self.mock_db, self.mock_mpesa)
        
        # Mock PRICING
        self.patcher = patch('payment_flow.PRICING', {
            INDIVIDUAL_TIER: {"name": "Individual", "amount": 8500},
            TEAM_TIER: {"name": "Team", "amount": 6500}
        })
        self.mock_pricing = self.patcher.start()
        
    def tearDown(self):
        self.patcher.stop()
        
    def test_initiate_individual_purchase(self):
        """Test initiating payment for individual plan"""
        user_id = "user_123"
        org_id = "org_456"
        phone = "254700000000"
        
        # Mock M-Pesa response
        self.mock_mpesa.initiate_stk_push.return_value = {
            "ResponseCode": "0",
            "CheckoutRequestID": "ws_CO_12345"
        }
        
        result = self.payment_manager.initiate_organization_purchase(
            user_id, org_id, INDIVIDUAL_TIER, 1, phone
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["amount"], 8500)
        
        # Verify DB call
        self.mock_db.create_payment_transaction.assert_called_once()
        args, kwargs = self.mock_db.create_payment_transaction.call_args
        
        self.assertEqual(kwargs["amount"], 8500)
        self.assertEqual(kwargs["seats"], 1)
        self.assertEqual(kwargs["tier"], INDIVIDUAL_TIER)
        
    def test_initiate_team_purchase(self):
        """Test initiating payment for team plan with multiple seats"""
        user_id = "user_123"
        org_id = "org_456"
        phone = "254700000000"
        seats = 5
        expected_amount = 6500 * 5
        
        self.mock_mpesa.initiate_stk_push.return_value = {
            "ResponseCode": "0",
            "CheckoutRequestID": "ws_CO_67890"
        }
        
        result = self.payment_manager.initiate_organization_purchase(
            user_id, org_id, TEAM_TIER, seats, phone
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(result["amount"], expected_amount)
        
        # Verify DB call
        self.mock_db.create_payment_transaction.assert_called_once()
        args, kwargs = self.mock_db.create_payment_transaction.call_args
        
        self.assertEqual(kwargs["amount"], expected_amount)
        self.assertEqual(kwargs["seats"], seats)
        self.assertEqual(kwargs["tier"], TEAM_TIER)

    def test_verify_payment_success(self):
        """Test successful payment verification creating org subscription"""
        checkout_id = "ws_CO_12345"
        user_id = "user_123"
        org_id = "org_456"
        
        # Mock transaction record
        self.mock_db.get_payment_transaction_by_checkout_id.return_value = {
            "payment_status": "pending",
            "transaction_type": "organization_subscription",
            "amount": 8500,
            "metadata": {
                "organization_id": org_id,
                "tier": INDIVIDUAL_TIER,
                "seats": 1
            }
        }
        
        # Mock M-Pesa query response
        self.mock_mpesa.query_stk_push.return_value = {
            "ResultCode": "0",
            "MpesaReceiptNumber": "PAY12345"
        }
        
        result = self.payment_manager.verify_and_process_payment(checkout_id, user_id, max_attempts=1)
        
        self.assertTrue(result["success"])
        
        # Verify subscription creation
        self.mock_db.create_organization_subscription.assert_called_once()
        args, kwargs = self.mock_db.create_organization_subscription.call_args
        
        self.assertEqual(kwargs["organization_id"], org_id)
        self.assertEqual(kwargs["subscription_tier"], INDIVIDUAL_TIER)
        self.assertEqual(kwargs["seats_purchased"], 1)

if __name__ == "__main__":
    unittest.main()
