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
from subscription_manager import (
    SubscriptionManager, PRICING,
    INDIVIDUAL_TIER, TEAM_TIER, ENTERPRISE_TIER,
)


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

            # PRICING amounts are stored in minor units (KSh × 100)
            # e.g. 650000 = KES 6,500.  Divide by 100 to get actual KES.
            price_per_seat_kes = tier_config["amount"] // 100

            if tier == INDIVIDUAL_TIER:
                seats = 1  # Force 1 seat for individual
                amount = price_per_seat_kes
            elif tier == TEAM_TIER:
                min_seats = tier_config.get("min_seats", 3)
                seats = max(seats, min_seats)  # Enforce minimum
                amount = price_per_seat_kes * seats
            elif tier == ENTERPRISE_TIER:
                min_seats = tier_config.get("min_seats", 10)
                seats = max(seats, min_seats)  # Enforce minimum
                amount = price_per_seat_kes * seats
            else:
                amount = price_per_seat_kes * seats

            logger.info(
                f"Payment amount calculated: {tier} x {seats} seats = "
                f"KES {amount:,} (price_per_seat=KES {price_per_seat_kes:,})"
            )
            
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
                tx = self.db.create_payment_transaction(
                    user_id=user_id,
                    amount=amount,
                    transaction_type="subscription",  # Changed from "organization_subscription" to match DB constraint
                    checkout_request_id=checkout_request_id,
                    phone_number_hash=phone_hash,
                    credits_purchased=0,
                    organization_id=organization_id,
                    seats=seats,
                    tier=tier
                )
                
                if not tx:
                    logger.error(f"Failed to create payment transaction record in database for {checkout_request_id}")
                    return {
                        "success": False,
                        "message": "Payment system initialization failed. Please try again."
                    }
                
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
                    # ── PRIORITY 1: Check Callback Table ───────────────────
                    # Authoritative result from Safaricom via Edge Function
                    callback = self.db.get_mpesa_callback(checkout_request_id)
                    
                    if callback:
                        status = callback.get("status")
                        result_code = str(callback.get("result_code", ""))
                        
                        if status == "success" or result_code == "0":
                            receipt_number = callback.get("mpesa_receipt_number", "")
                            
                            # Update transaction status in our main table
                            self.db.update_payment_status(
                                checkout_request_id=checkout_request_id,
                                status="completed",
                                receipt_number=receipt_number
                            )
                            
                            logger.info(f"Payment verified via callback for {checkout_request_id}")
                            return self._finalize_payment(transaction, user_id, receipt_number)
                            
                        elif status == "failed" or result_code in ["1032", "1037", "1"]:
                            self.db.update_payment_status(
                                checkout_request_id=checkout_request_id,
                                status="failed"
                            )
                            logger.warning(f"Payment failed via callback for {checkout_request_id}")
                            return {
                                "success": False,
                                "message": "Payment was cancelled or failed. Please try again."
                            }

                    # ── PRIORITY 2: Fallback to Query API ──────────────────
                    # Direct check with Safaricom if callback is delayed
                    response = self.mpesa.query_stk_push(checkout_request_id)
                    result_code = str(response.get("ResultCode", ""))
                    
                    if result_code == "0":
                        receipt_number = response.get("MpesaReceiptNumber", "")
                        self.db.update_payment_status(
                            checkout_request_id=checkout_request_id,
                            status="completed",
                            receipt_number=receipt_number
                        )
                        logger.info(f"Payment verified via Query API for {checkout_request_id}")
                        return self._finalize_payment(transaction, user_id, receipt_number)
                    
                    elif result_code in ["1032", "1037", "1"]:
                        self.db.update_payment_status(
                            checkout_request_id=checkout_request_id,
                            status="failed"
                        )
                        logger.warning(f"Payment failed via Query API for {checkout_request_id}")
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

    def _finalize_payment(self, transaction: Dict[str, Any], user_id: str, receipt_number: str) -> Dict[str, Any]:
        """
        Finalize a successful payment by updating subscriptions or credits.
        """
        try:
            transaction_type = transaction.get("transaction_type")
            checkout_request_id = transaction.get("checkout_request_id")

            if transaction_type in ["subscription", "organization_subscription"]:
                metadata = transaction.get("metadata") or {}
                organization_id = metadata.get("organization_id")
                seats = int(metadata.get("seats", 1))
                tier = metadata.get("tier", "individual")

                if not organization_id:
                    logger.error(f"organization_subscription missing organization_id in metadata for tx {checkout_request_id}")
                    return {
                        "success": False,
                        "message": "Payment recorded but subscription activation failed. Please contact support."
                    }

                # Activate subscription via SubscriptionManager
                upgraded = self.subscription_mgr.upgrade_to_tier(
                    user_id=user_id,
                    new_tier=tier,
                    seats=seats
                )

                if upgraded:
                    logger.info(f"Activated {tier} subscription for org {organization_id} ({seats} seats)")
                    return {
                        "success": True,
                        "message": f"Payment successful! {tier.title()} plan is now active.",
                        "tier": tier
                    }
                else:
                    logger.error(f"upgrade_to_tier failed for org {organization_id} after successful payment {checkout_request_id}")
                    return {
                        "success": False,
                        "message": f"Payment received but subscription activation failed. Please contact support with receipt number: {receipt_number}"
                    }

            elif transaction_type == "credit_purchase":
                credits = transaction.get("credits_purchased") or 0
                
                # Update user's credit balance
                updated_sub = self.db.update_subscription_credits(user_id, credits)
                
                if updated_sub:
                    logger.info(f"Added {credits} credits for user {user_id}")
                    return {
                        "success": True,
                        "credits_added": credits,
                        "message": f"Payment successful! {credits} credits have been added to your account."
                    }
                else:
                    logger.error(f"Failed to update credits for user {user_id} after payment {checkout_request_id}")
                    return {
                        "success": False,
                        "message": "Payment received but credits update failed. Please contact support."
                    }

            else:
                logger.error(f"Unknown transaction_type '{transaction_type}' for checkout {checkout_request_id}")
                return {
                    "success": False,
                    "message": "Unrecognized payment type. Please contact support."
                }
        except Exception as e:
            logger.error(f"Error finalizing payment: {e}", exc_info=True)
            return {
                "success": False,
                "message": "Payment verified but finalization failed. Please contact support."
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
