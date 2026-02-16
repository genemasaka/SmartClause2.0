"""
Unit tests for Payment Flow Manager
Tests payment initiation, verification, and subscription updates
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from payment_flow import PaymentFlowManager
from subscription_manager import SINGLE_CREDIT_TIER, PAY_AS_YOU_GO_TIER, STANDARD_TIER

class TestPaymentFlowManager(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_mpesa = MagicMock()
        self.mock_mpesa.encryptor = MagicMock()
        self.mock_mpesa.encryptor.hash_data.return_value = "hashed_phone"
        
        self.payment_flow = PaymentFlowManager(
            db_manager=self.mock_db,
            mpesa_handler=self.mock_mpesa
        )
    
    def test_initiate_credit_purchase_single_credit_success(self):
        """Test successful Single Credit purchase initiation"""
        # Setup
        self.mock_mpesa.initiate_stk_push.return_value = {
            "ResponseCode": "0",
            "CheckoutRequestID": "ws_CO_123456"
        }
        
        # Execute
        result = self.payment_flow.initiate_credit_purchase(
            user_id="user_123",
            phone_number="254712345678",
            tier=SINGLE_CREDIT_TIER
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["checkout_request_id"], "ws_CO_123456")
        self.assertEqual(result["credits"], 1)
        self.assertEqual(result["amount"], 950)
        
        # Verify STK push was called with correct amount
        self.mock_mpesa.initiate_stk_push.assert_called_once()
        call_args = self.mock_mpesa.initiate_stk_push.call_args[1]
        self.assertEqual(call_args["amount"], 950)
        
        # Verify transaction was created
        self.mock_db.create_payment_transaction.assert_called_once()
    
    def test_initiate_credit_purchase_payg_success(self):
        """Test successful Pay-As-You-Go credit purchase initiation"""
        # Setup
        self.mock_mpesa.initiate_stk_push.return_value = {
            "ResponseCode": "0",
            "CheckoutRequestID": "ws_CO_789012"
        }
        
        # Execute
        result = self.payment_flow.initiate_credit_purchase(
            user_id="user_456",
            phone_number="254723456789",
            tier=PAY_AS_YOU_GO_TIER
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["credits"], 10)
        self.assertEqual(result["amount"], 6000)
    
    def test_initiate_credit_purchase_invalid_tier(self):
        """Test credit purchase with invalid tier"""
        result = self.payment_flow.initiate_credit_purchase(
            user_id="user_123",
            phone_number="254712345678",
            tier=STANDARD_TIER  # Invalid for credit purchase
        )
        
        self.assertFalse(result["success"])
        self.assertIn("Invalid tier", result["message"])
    
    def test_initiate_subscription_purchase_success(self):
        """Test successful Standard subscription purchase"""
        # Setup
        self.mock_mpesa.initiate_stk_push.return_value = {
            "ResponseCode": "0",
            "CheckoutRequestID": "ws_CO_SUB123"
        }
        
        # Execute
        result = self.payment_flow.initiate_subscription_purchase(
            user_id="user_789",
            phone_number="254734567890"
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["amount"], 7500)
        
        # Verify transaction was created with correct type
        self.mock_db.create_payment_transaction.assert_called_once()
        call_args = self.mock_db.create_payment_transaction.call_args[1]
        self.assertEqual(call_args["transaction_type"], "subscription")
    
    def test_verify_and_process_payment_credit_success(self):
        """Test successful payment verification for credit purchase"""
        # Setup
        self.mock_db.get_payment_transaction_by_checkout_id.return_value = {
            "checkout_request_id": "ws_CO_123",
            "payment_status": "pending",
            "transaction_type": "credit_purchase",
            "credits_purchased": 10
        }
        
        self.mock_mpesa.query_stk_push.return_value = {
            "ResultCode": "0",
            "MpesaReceiptNumber": "RCT123456"
        }
        
        # Execute
        result = self.payment_flow.verify_and_process_payment(
            checkout_request_id="ws_CO_123",
            user_id="user_123",
            max_attempts=1
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertEqual(result["credits_added"], 10)
        
        # Verify status was updated
        self.mock_db.update_payment_status.assert_called_once_with(
            checkout_request_id="ws_CO_123",
            status="completed",
            receipt_number="RCT123456"
        )
    
    def test_verify_and_process_payment_subscription_success(self):
        """Test successful payment verification for subscription"""
        # Setup
        self.mock_db.get_payment_transaction_by_checkout_id.return_value = {
            "checkout_request_id": "ws_CO_SUB",
            "payment_status": "pending",
            "transaction_type": "subscription",
            "credits_purchased": 0
        }
        
        self.mock_mpesa.query_stk_push.return_value = {
            "ResultCode": "0",
            "MpesaReceiptNumber": "RCT789012"
        }
        
        # Execute
        result = self.payment_flow.verify_and_process_payment(
            checkout_request_id="ws_CO_SUB",
            user_id="user_456",
            max_attempts=1
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertIn("subscription_end_date", result)
    
    def test_verify_and_process_payment_failed(self):
        """Test payment verification when payment failed"""
        # Setup
        self.mock_db.get_payment_transaction_by_checkout_id.return_value = {
            "checkout_request_id": "ws_CO_FAIL",
            "payment_status": "pending",
            "transaction_type": "credit_purchase",
            "credits_purchased": 1
        }
        
        self.mock_mpesa.query_stk_push.return_value = {
            "ResultCode": "1032"  # User cancelled
        }
        
        # Execute
        result = self.payment_flow.verify_and_process_payment(
            checkout_request_id="ws_CO_FAIL",
            user_id="user_789",
            max_attempts=1
        )
        
        # Assert
        self.assertFalse(result["success"])
        
        # Verify status was updated to failed
        self.mock_db.update_payment_status.assert_called_once_with(
            checkout_request_id="ws_CO_FAIL",
            status="failed"
        )
    
    def test_verify_and_process_payment_already_processed(self):
        """Test verification of already processed payment"""
        # Setup
        self.mock_db.get_payment_transaction_by_checkout_id.return_value = {
            "checkout_request_id": "ws_CO_DONE",
            "payment_status": "completed",
            "transaction_type": "credit_purchase",
            "credits_purchased": 10
        }
        
        # Execute
        result = self.payment_flow.verify_and_process_payment(
            checkout_request_id="ws_CO_DONE",
            user_id="user_123",
            max_attempts=1
        )
        
        # Assert
        self.assertTrue(result["success"])
        self.assertTrue(result.get("already_processed"))
        
        # Verify no M-Pesa query was made
        self.mock_mpesa.query_stk_push.assert_not_called()
    
    def test_get_pending_payment(self):
        """Test retrieving pending payment"""
        # Setup
        recent_time = datetime.now().isoformat()
        self.mock_db.get_user_payment_history.return_value = [
            {
                "checkout_request_id": "ws_CO_PENDING",
                "payment_status": "pending",
                "transaction_date": recent_time
            },
            {
                "checkout_request_id": "ws_CO_OLD",
                "payment_status": "completed",
                "transaction_date": recent_time
            }
        ]
        
        # Execute
        result = self.payment_flow.get_pending_payment("user_123")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["checkout_request_id"], "ws_CO_PENDING")

if __name__ == '__main__':
    unittest.main()
