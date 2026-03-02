"""
Unit tests for Payment Flow Manager
Tests organization subscription initiation, verification, and processing
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from payment_flow import PaymentFlowManager
from subscription_manager import INDIVIDUAL_TIER, TEAM_TIER, ENTERPRISE_TIER

class TestPaymentFlowManager(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_mpesa = MagicMock()
        self.mock_mpesa.encryptor = MagicMock()
        self.mock_mpesa.encryptor.hash_data.return_value = "hashed_phone"
        
        self.mock_subscription_mgr = MagicMock()
        
        self.payment_flow = PaymentFlowManager(
            db_manager=self.mock_db,
            mpesa_handler=self.mock_mpesa
        )
        self.payment_flow.subscription_mgr = self.mock_subscription_mgr
    
    def test_initiate_organization_purchase_success(self):
        """Test successful organization subscription initiation"""
        # Setup
        self.mock_mpesa.initiate_stk_push.return_value = {
            "ResponseCode": "0",
            "CheckoutRequestID": "ws_CO_123456"
        }
        self.mock_db.create_payment_transaction.return_value = {"id": "tx_123"}
        
        # Execute
        result = self.payment_flow.initiate_organization_purchase(
            user_id="user_123",
            organization_id="org_123",
            tier=INDIVIDUAL_TIER,
            seats=1,
            phone_number="254712345678"
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["checkout_request_id"], "ws_CO_123456")
        
        # Verify STK push was called
        self.mock_mpesa.initiate_stk_push.assert_called_once()
        
        # Verify transaction was created with correct type
        self.mock_db.create_payment_transaction.assert_called_once()
        call_args = self.mock_db.create_payment_transaction.call_args[1]
        self.assertEqual(call_args["transaction_type"], "subscription")
        self.assertEqual(call_args["organization_id"], "org_123")

    def test_verify_and_process_subscription_success(self):
        """Test successful payment verification for subscription"""
        # Setup
        self.mock_db.get_payment_transaction_by_checkout_id.return_value = {
            "checkout_request_id": "ws_CO_123",
            "payment_status": "pending",
            "transaction_type": "subscription",
            "metadata": {"organization_id": "org_123", "tier": "individual", "seats": 1}
        }
        
        self.mock_mpesa.query_stk_push.return_value = {
            "ResultCode": "0",
            "MpesaReceiptNumber": "RCT123456"
        }
        
        self.mock_subscription_mgr.upgrade_to_tier.return_value = True
        
        # Execute
        result = self.payment_flow.verify_and_process_payment(
            checkout_request_id="ws_CO_123",
            user_id="user_123",
            max_attempts=1
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["tier"], "individual")
        
        # Verify status was updated
        self.mock_db.update_payment_status.assert_called_once_with(
            checkout_request_id="ws_CO_123",
            status="completed",
            receipt_number="RCT123456"
        )
        
        # Verify subscription was upgraded
        self.mock_subscription_mgr.upgrade_to_tier.assert_called_once_with(
            user_id="user_123",
            new_tier="individual",
            seats=1
        )

    def test_verify_and_process_payment_credit_success(self):
        """Test successful payment verification for credit purchase (legacy/schema support)"""
        # Setup
        self.mock_db.get_payment_transaction_by_checkout_id.return_value = {
            "checkout_request_id": "ws_CO_CREDIT",
            "payment_status": "pending",
            "transaction_type": "credit_purchase",
            "credits_purchased": 10
        }
        
        self.mock_mpesa.query_stk_push.return_value = {
            "ResultCode": "0",
            "MpesaReceiptNumber": "RCT_CREDIT"
        }
        
        self.mock_db.update_subscription_credits.return_value = {"id": "sub_123"}
        
        # Execute
        result = self.payment_flow.verify_and_process_payment(
            checkout_request_id="ws_CO_CREDIT",
            user_id="user_123",
            max_attempts=1
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["credits_added"], 10)

    def test_verify_and_process_payment_not_found(self):
        """Test verification when transaction record is missing (Graceful handling)"""
        # Setup
        self.mock_db.get_payment_transaction_by_checkout_id.return_value = None
        
        # Execute
        result = self.payment_flow.verify_and_process_payment(
            checkout_request_id="ws_CO_MISSING",
            user_id="user_123",
            max_attempts=1
        )
        
        # Assert
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "Transaction not found")

if __name__ == '__main__':
    unittest.main()
