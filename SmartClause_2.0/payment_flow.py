"""
Payment Flow Manager for SmartClause Paywall
Orchestrates M-Pesa payment processing and subscription updates
"""

import sys
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time

# Add parent directory to path to import mpesa_handler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mpesa_handler import MpesaHandler
from database import DatabaseManager
from subscription_manager import SubscriptionManager, PRICING

logger = logging.getLogger(__name__)

class PaymentFlowManager:
    """
    Manages the complete payment workflow from initiation to verification
    and subscription updates.
    """
    
    def __init__(self, db_manager: DatabaseManager, mpesa_handler: MpesaHandler = None):
        self.db = db_manager
        self.mpesa = mpesa_handler or MpesaHandler()
        self.subscription_mgr = SubscriptionManager(db_manager)
    
    
    def initiate_organization_purchase(self, user_id: str, organization_id: str, tier: str, seats: int, phone_number: str) -> Dict[str, Any]:
        """
        Initiate organization subscription purchase.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            tier: Subscription tier (INDIVIDUAL, TEAM, ENTERPRISE)
            seats: Number of seats (minimum 1)
            phone_number: M-Pesa phone number
            
        Returns:
            Dict with status, checkout_request_id, and message
        """
        try:
            tier_config = PRICING.get(tier)
            if not tier_config:
                 return {
                    "success": False,
                    "message": "Invalid subscription tier"
                }

            price_per_seat = tier_config["amount"]
            
            if tier == "individual":
                seats = 1 # Force 1 seat for individual
                amount = price_per_seat
            else:
                 amount = price_per_seat * seats
            
            # Hash phone number for privacy
            phone_hash = self.mpesa.encryptor.hash_data(phone_number)
            
            # Initiate STK push
            response = self.mpesa.initiate_stk_push(
                phone_number=phone_number,
                amount=amount,
                transaction_desc=f"SmartClause {tier.title()} ({seats} Users)",
                account_reference=f"ORG_{organization_id[:8]}"
            )
            
            # Check if STK push was successful
            if response.get("ResponseCode") == "0":
                checkout_request_id = response.get("CheckoutRequestID")
                
                # Create payment transaction record with metadata
                self.db.create_payment_transaction(
                    user_id=user_id,
                    amount=amount,
                    transaction_type="organization_subscription",
                    checkout_request_id=checkout_request_id,
                    phone_number_hash=phone_hash,
                    credits_purchased=0,
                    organization_id=organization_id,
                    seats=seats,
                    tier=tier
                )
                
                logger.info(f"Organization subscription purchase initiated for org {organization_id}, tier {tier}, seats {seats}")
                
                return {
                    "success": True,
                    "checkout_request_id": checkout_request_id,
                    "amount": amount,
                    "message": "Payment request sent. Please check your phone."
                }
            else:
                error_msg = response.get("errorMessage", "Payment initiation failed")
                logger.error(f"STK push failed for org {organization_id}: {error_msg}")
                return {
                    "success": False,
                    "message": error_msg
                }
                
        except Exception as e:
            logger.error(f"Error initiating organization purchase: {e}", exc_info=True)
            return {
                "success": False,
                "message": "An error occurred. Please try again."
            }
    
    
    def verify_and_process_payment(
        self, 
        checkout_request_id: str, 
        user_id: str,
        max_attempts: int = 6,
        delay: int = 5
    ) -> Dict[str, Any]:
        """
        Verify payment and process subscription/credit updates.
        
        Args:
            checkout_request_id: M-Pesa checkout request ID
            user_id: User ID
            max_attempts: Maximum verification attempts
            delay: Delay between attempts in seconds
            
        Returns:
            Dict with verification status and details
        """
        try:
            # Get transaction record
            transaction = self.db.get_payment_transaction_by_checkout_id(checkout_request_id)
            if not transaction:
                return {
                    "success": False,
                    "message": "Transaction not found"
                }
            
            # Check if already processed
            if transaction.get("payment_status") == "completed":
                return {
                    "success": True,
                    "already_processed": True,
                    "message": "Payment already processed"
                }
            
            # Verify payment with retries
            attempts = 0
            while attempts < max_attempts:
                try:
                    response = self.mpesa.query_stk_push(checkout_request_id)
                    result_code = str(response.get("ResultCode", ""))
                    
                    if result_code == "0":
                        # Payment successful
                        receipt_number = response.get("MpesaReceiptNumber", "")
                        
                        # Update transaction status
                        self.db.update_payment_status(
                            checkout_request_id=checkout_request_id,
                            status="completed",
                            receipt_number=receipt_number
                        )
                        
                        # Process payment based on transaction type
                        transaction_type = transaction.get("transaction_type")
                        credits_purchased = transaction.get("credits_purchased", 0)
                        
                        if transaction_type == "credit_purchase":
                            # Add credits to user account
                            self.subscription_mgr.add_credits(user_id, credits_purchased)
                            logger.info(f"Added {credits_purchased} credits to user {user_id}")
                            
                            return {
                                "success": True,
                                "message": f"Payment successful! {credits_purchased} credit(s) added.",
                                "credits_added": credits_purchased
                            }
                            
                        elif transaction_type == "subscription":
                            # Upgrade to Standard tier
                            end_date = (datetime.now() + timedelta(days=30)).isoformat()
                            self.subscription_mgr.upgrade_to_standard(user_id, end_date)
                            logger.info(f"Upgraded user {user_id} to Standard tier")
                            
                            return {
                                "success": True,
                                "message": "Payment successful! You now have Standard access.",
                                "subscription_end_date": end_date
                            }
                        
                        elif transaction_type == "organization_subscription":
                             # Create organization subscription
                             organization_id = transaction.get("metadata", {}).get("organization_id")
                             seats = transaction.get("metadata", {}).get("seats", 1)
                             tier = transaction.get("metadata", {}).get("tier", "individual")
                             
                             if organization_id:
                                 self.db.create_organization_subscription(
                                     organization_id=organization_id,
                                     subscription_tier=tier,
                                     seats_purchased=seats,
                                     price_per_seat=int(transaction.get("amount", 0) / seats) if seats > 0 else 0
                                 )
                                 logger.info(f"Activated {tier} subscription for organization {organization_id}")
                                 
                                 return {
                                     "success": True,
                                     "message": f"Payment successful! {tier.title()} subscription active.",
                                     "tier": tier
                                 }
                    
                    elif result_code in ["1032", "1037", "1"]:
                        # Payment failed or cancelled
                        self.db.update_payment_status(
                            checkout_request_id=checkout_request_id,
                            status="failed"
                        )
                        
                        logger.warning(f"Payment failed for user {user_id}, result code: {result_code}")
                        
                        return {
                            "success": False,
                            "message": "Payment was cancelled or failed. Please try again."
                        }
                    
                    # Still pending, wait and retry
                    time.sleep(delay)
                    attempts += 1
                    
                except Exception as e:
                    logger.error(f"Error during verification attempt {attempts}: {e}")
                    attempts += 1
                    time.sleep(delay)
            
            # Max attempts reached
            logger.warning(f"Payment verification timeout for user {user_id}")
            return {
                "success": False,
                "message": "Payment verification timed out. Please contact support if amount was deducted."
            }
            
        except Exception as e:
            logger.error(f"Error verifying payment: {e}", exc_info=True)
            return {
                "success": False,
                "message": "An error occurred during verification. Please try again."
            }
    
    def get_pending_payment(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's most recent pending payment transaction.
        
        Args:
            user_id: User ID
            
        Returns:
            Transaction dict or None
        """
        try:
            transactions = self.db.get_user_payment_history(user_id)
            for tx in transactions:
                if tx.get("payment_status") == "pending":
                    # Check if not too old (30 minutes)
                    tx_date = datetime.fromisoformat(tx.get("transaction_date").replace('Z', '+00:00'))
                    age = datetime.now(tx_date.tzinfo) - tx_date
                    if age.total_seconds() < 1800:  # 30 minutes
                        return tx
            return None
        except Exception as e:
            logger.error(f"Error getting pending payment: {e}")
            return None
