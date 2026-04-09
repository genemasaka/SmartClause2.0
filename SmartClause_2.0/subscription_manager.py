"""
Subscription Manager - Enterprise Subscription Model
Handles subscription logic for Individual, Team, and Enterprise tiers
Compatible with organization-based subscription architecture
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from organization_manager import OrganizationManager, SubscriptionTier, get_user_role_from_org

logger = logging.getLogger(__name__)

# Tier Configuration
TRIAL_TIER = SubscriptionTier.TRIAL.value
INDIVIDUAL_TIER = SubscriptionTier.INDIVIDUAL.value
TEAM_TIER = SubscriptionTier.TEAM.value
ENTERPRISE_TIER = SubscriptionTier.ENTERPRISE.value

# Pricing Configuration
# All monetary amounts are stored in KSh minor units (× 100).
# e.g. KSh 6,500/seat is stored as 650_000. Divide by 100 for display.
PRICING = {
    TRIAL_TIER: {
        "amount": 0,
        "documents_per_month": 7,  # 7 documents allowed during 7-day trial
        "name": "Free Trial",
        "per_user": False,
        "trial_days": 7
    },
    INDIVIDUAL_TIER: {
        "amount": 850000,  # KSh 8,500
        "documents_per_month": 50,
        "name": "Individual",
        "per_user": True
    },
    TEAM_TIER: {
        "amount": 650000,  # KSh 6,500 per user
        "documents_per_month": 100,
        "name": "Team",
        "per_user": True,
        "min_seats": 3
    },
    ENTERPRISE_TIER: {
        "amount": 500000,  # KSh 5,000 per user
        "documents_per_month": None,  # Unlimited
        "name": "Enterprise",
        "per_user": True,
        "min_seats": 10
    }
}

# Feature Flags
# Trial users get access to core features (document_editor, ai_chatbot) but NOT premium features
FEATURES = {
    "document_editor": [INDIVIDUAL_TIER, TEAM_TIER, ENTERPRISE_TIER],
    "clause_library": [INDIVIDUAL_TIER, TEAM_TIER, ENTERPRISE_TIER],
    "admin_dashboard": [TEAM_TIER, ENTERPRISE_TIER],
    "sso": [ENTERPRISE_TIER],
    "api_access": [ENTERPRISE_TIER],
    "custom_templates": [TEAM_TIER, ENTERPRISE_TIER],
    "priority_support": [TEAM_TIER, ENTERPRISE_TIER],
    "ai_chatbot": [INDIVIDUAL_TIER, TEAM_TIER, ENTERPRISE_TIER],
}


class SubscriptionManager:
    """
    Handles all subscription logic including:
    - User status checks
    - Feature access validation
    - Document limit enforcement
    - Subscription expiration
    
    NOTE: This is a compatibility layer that works with both the old credit-based 
    system and the new organization-based system.
    """
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.org_manager = OrganizationManager(db_manager)
    
    def get_user_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive status of user's subscription.
        Returns a dict with tier, usage limits, active status, etc.
        """
        try:
            # Get user's organization
            org = self.org_manager.get_user_organization(user_id)

            if not org:
                # No organization found — treat as new trial user
                trial_doc_limit = PRICING.get(TRIAL_TIER, {}).get('documents_per_month', 7)
                return {
                    "tier": TRIAL_TIER,
                    "documents_remaining": trial_doc_limit,  # 7 docs during trial
                    "is_active": True,
                    "expiry_date": None,
                    "days_remaining": None,
                    "organization_id": None,
                    "organization_name": "Personal",
                    "role": "owner"
                }

            # Safe role extraction — look up by user_id, not by index position.
            # Using index 0 is fragile: the query may return members in any order,
            # silently granting the wrong role to a regular member.
            user_id_for_role = user_id  # captured from the outer argument
            role = get_user_role_from_org(org, user_id_for_role)

            # Get organization subscription
            subscription = self.org_manager.get_organization_subscription(org['id'])

            if not subscription:
                # Org exists but no paid subscription — determine trial state
                tier = org.get('subscription_tier', TRIAL_TIER)
                is_active, days_remaining = self._check_trial_status(org)
                return {
                    "tier": tier,
                    "documents_remaining": None if is_active else 0,
                    "is_active": is_active,
                    "expiry_date": org.get('trial_end_date'),
                    "days_remaining": days_remaining,
                    "organization_id": org['id'],
                    "organization_name": org.get('name', 'Personal'),
                    "role": role
                }

            # Paid subscription — calculate usage and expiry
            tier = subscription['subscription_tier']
            plan_config = PRICING.get(tier, {})
            documents_limit = plan_config.get('documents_per_month')

            # Check if subscription is active and not expired
            is_active = subscription.get('status') == 'active'
            days_remaining = None
            if subscription.get('current_period_end'):
                try:
                    end_date = datetime.fromisoformat(
                        subscription['current_period_end'].replace('Z', '+00:00')
                    )
                    now = datetime.now(end_date.tzinfo)
                    if now > end_date:
                        is_active = False
                    else:
                        days_remaining = (end_date - now).days + 1
                except Exception:
                    pass

            # Calculate remaining documents
            if documents_limit is not None and is_active:
                try:
                    usage = self.db.get_user_document_usage(
                        user_id,
                        datetime.fromisoformat(
                            subscription['current_period_start'].replace('Z', '+00:00')
                        ),
                        datetime.fromisoformat(
                            subscription['current_period_end'].replace('Z', '+00:00')
                        )
                    )
                    documents_remaining = max(0, documents_limit - usage)
                except Exception:
                    documents_remaining = documents_limit  # Fallback: assume full quota
            else:
                documents_remaining = None  # Unlimited (Enterprise/Trial)

            return {
                "tier": tier,
                "documents_remaining": documents_remaining,
                "is_active": is_active,
                "expiry_date": subscription.get('current_period_end'),
                "days_remaining": days_remaining,
                "organization_id": org['id'],
                "organization_name": org.get('name', 'Personal'),
                "role": role,
                "seats_purchased": subscription.get('seats_purchased'),
                "seats_used": subscription.get('seats_used')
            }

        except Exception as e:
            # DESIGN DECISION: We intentionally fail open (return trial-active state)
            # on unexpected errors to avoid blocking users during a DB outage or bug.
            # This is a conscious trade-off. Set up alerting on CRITICAL log lines from
            # this function so the team is immediately aware when it triggers.
            # To change this behaviour, set SMARTCLAUSE_FAIL_OPEN=false in env.
            import os
            if os.getenv("SMARTCLAUSE_FAIL_OPEN", "true").lower() != "false":
                logger.critical(
                    f"get_user_status FAILING OPEN for user {user_id}: {e}. "
                    "User is being granted trial-active access. Investigate immediately."
                )
                trial_doc_limit = PRICING.get(TRIAL_TIER, {}).get('documents_per_month', 7)
                return {
                    "tier": TRIAL_TIER,
                    "documents_remaining": trial_doc_limit,
                    "is_active": True,
                    "expiry_date": None,
                    "days_remaining": None,
                    "organization_id": None,
                    "organization_name": "Personal",
                    "role": "member"
                }
            else:
                logger.error(f"Error fetching user status for {user_id}: {e}")
                raise
    
    def has_access(self, user_id: str, feature_key: str) -> bool:
        """
        Check if user has access to a specific feature.
        Returns False if the subscription is inactive or the feature is not available on their tier.
        """
        try:
            status = self.get_user_status(user_id)
            tier = status["tier"]
            is_active = status["is_active"]

            if not is_active:
                return False

            allowed_tiers = FEATURES.get(feature_key, [])
            return tier in allowed_tiers
        except Exception as e:
            logger.error(f"Error checking feature access for {user_id}/{feature_key}: {e}")
            return False  # Fail closed on errors
    
    def can_generate_document(self, user_id: str) -> tuple[bool, str]:
        """
        Check if user can generate a document.
        Returns (can_generate, reason)
        """
        # Use organization manager's method which handles all the logic
        can_create, reason = self.org_manager.can_create_document(user_id)
        return can_create, reason
    
    def record_document_generation(self, user_id: str, document_type: str = 'general') -> bool:
        """
        Record that a document was generated.
        Uses organization manager to record usage.
        """
        try:
            return self.org_manager.record_document_creation(user_id, document_type)
        except Exception as e:
            logger.error(f"Failed to record document generation: {e}")
            return False
    
    def initialize_user_subscription(self, user_id: str, user_email: str, user_name: Optional[str] = None):
        """
        Create default organization and subscription for new user.
        """
        try:
            org, was_created = self.org_manager.get_or_create_organization_for_user(
                user_id, user_email, user_name
            )
            
            if was_created:
                logger.info(f"Created new organization for user {user_id}: {org['name']}")
            else:
                logger.info(f"User {user_id} joined existing organization: {org['name']}")
            
            return org
        
        except Exception as e:
            logger.error(f"Failed to initialize user subscription: {e}")
            return None
    
    def upgrade_to_tier(
        self,
        user_id: str,
        new_tier: str,
        seats: int = 1,
        billing_cycle: str = 'monthly'
    ) -> bool:
        """
        Upgrade user's organization to a new tier.
        """
        try:
            # Get user's organization
            org = self.org_manager.get_user_organization(user_id)
            
            if not org:
                logger.error(f"User {user_id} has no organization")
                return False
            
            # Validate tier
            if new_tier not in [INDIVIDUAL_TIER, TEAM_TIER, ENTERPRISE_TIER]:
                logger.error(f"Invalid tier: {new_tier}")
                return False
            
            # Validate seats for team/enterprise
            min_seats = PRICING[new_tier].get('min_seats', 1)
            if seats < min_seats:
                logger.error(f"{new_tier} requires minimum {min_seats} seats")
                return False
            
            price_per_seat = PRICING[new_tier]['amount']

            # Single atomic call: updates organizations AND organization_subscriptions
            # in one Postgres transaction. If either write fails, both roll back.
            response = self.db.upgrade_org_tier_atomic(
                organization_id=org['id'],
                new_tier=new_tier,
                seats=seats,
                price_per_seat=price_per_seat
            )

            if not response.get('success'):
                logger.error(
                    f"Atomic upgrade failed for org {org['id']}: {response.get('error')}"
                )
                return False
            
            logger.info(f"Upgraded organization {org['id']} to {new_tier} with {seats} seats")
            return True
        
        except Exception as e:
            logger.error(f"Failed to upgrade tier: {e}")
            return False
    
    def get_organization_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get organization information for the user.
        """
        return self.org_manager.get_user_organization(user_id)
    
    def get_organization_subscription(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """
        Get organization subscription details.
        """
        return self.org_manager.get_organization_subscription(organization_id)
        
    def get_organization_members(self, user_id: str) -> list[Dict[str, Any]]:
        """
        Get members of user's organization (if user is admin).
        """
        org = self.org_manager.get_user_organization(user_id)
        
        if not org:
            return []
        
        # Check if user is admin or owner — look up by user_id, not by index
        role = get_user_role_from_org(org, user_id)
        if role not in ['owner', 'admin']:
            return []
        
        return self.org_manager.get_organization_members(org['id'])
    
    def get_organization_usage(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get organization-wide usage statistics (for admins).
        """
        org = self.org_manager.get_user_organization(user_id)
        
        if not org:
            return None
        
        # Check if user is admin or owner — look up by user_id, not by index
        role = get_user_role_from_org(org, user_id)
        if role not in ['owner', 'admin']:
            return None
        
        return self.org_manager.get_organization_usage_summary(org['id'])
    
    @staticmethod
    def get_pricing_info():
        """
        Get pricing information for all tiers.
        """
        return PRICING
    
    @staticmethod
    def get_tier_features(tier: str) -> list[str]:
        """
        Get list of features available for a tier.
        """
        return [feature for feature, tiers in FEATURES.items() if tier in tiers]

    def _check_trial_status(self, org: Dict[str, Any]) -> tuple[bool, Optional[int]]:
        """
        Determine whether a trial organization is still active.

        Args:
            org: Organization dict (must have 'created_at')

        Returns:
            (is_active: bool, days_remaining: int | None)
        """
        created_at_str = org.get('created_at')
        trial_days = PRICING.get(TRIAL_TIER, {}).get('trial_days', 7)

        if not created_at_str:
            # No creation date — treat as active trial, unknown days remaining
            return True, None

        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            trial_end = created_at + timedelta(days=trial_days)  # timedelta imported at top of file
            now = datetime.now(created_at.tzinfo)

            if now > trial_end:
                return False, 0

            days_remaining = (trial_end - now).days + 1
            return True, days_remaining

        except Exception as e:
            logger.warning(f"Could not parse trial expiry for org {org.get('id')}: {e}")
            return True, None

