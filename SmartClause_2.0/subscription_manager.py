"""
Subscription Manager - Enterprise Subscription Model
Handles subscription logic for Individual, Team, and Enterprise tiers
Compatible with organization-based subscription architecture
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from organization_manager import OrganizationManager, SubscriptionTier

logger = logging.getLogger(__name__)

# Tier Configuration
TRIAL_TIER = SubscriptionTier.TRIAL.value
INDIVIDUAL_TIER = SubscriptionTier.INDIVIDUAL.value
TEAM_TIER = SubscriptionTier.TEAM.value
ENTERPRISE_TIER = SubscriptionTier.ENTERPRISE.value

# Pricing Configuration (in KSh minor units - multiply by 100)
PRICING = {
    TRIAL_TIER: {
        "amount": 0,
        "documents_per_month": None,  # Unlimited for 14-day trial
        "name": "Free Trial",
        "per_user": False,
        "trial_days": 14
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
FEATURES = {
    "document_editor": [INDIVIDUAL_TIER, TEAM_TIER, ENTERPRISE_TIER],
    "clause_library": [INDIVIDUAL_TIER, TEAM_TIER, ENTERPRISE_TIER],
    "admin_dashboard": [TEAM_TIER, ENTERPRISE_TIER],
    "sso": [ENTERPRISE_TIER],
    "api_access": [ENTERPRISE_TIER],
    "custom_templates": [TEAM_TIER, ENTERPRISE_TIER],
    "priority_support": [TEAM_TIER, ENTERPRISE_TIER],
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
        # Get user's organization
        org = self.org_manager.get_user_organization(user_id)
        
        if not org:
            # No organization - return trial status
            return {
                "tier": TRIAL_TIER,
                "documents_remaining": 10,
                "is_active": True,
                "expiry_date": None,
                "organization_id": None,
                "organization_name": None,
                "role": None
            }
        
        # Get organization subscription
        subscription = self.org_manager.get_organization_subscription(org['id'])
        
        if not subscription:
            # Organization exists but no subscription
            tier = org.get('subscription_tier', TRIAL_TIER)
            return {
                "tier": tier,
                "documents_remaining": 10 if tier == TRIAL_TIER else 0,
                "is_active": tier == TRIAL_TIER,
                "expiry_date": org.get('trial_end_date'),
                "organization_id": org['id'],
                "organization_name": org['name'],
                "role": org.get('organization_members', [{}])[0].get('role')
            }
        
        # Calculate document usage
        tier = subscription['subscription_tier']
        plan_config = PRICING.get(tier, {})
        documents_limit = plan_config.get('documents_per_month')
        
        # Get current period usage
        if documents_limit is not None:
            usage = self.db.get_user_document_usage(
                user_id,
                datetime.fromisoformat(subscription['current_period_start'].replace('Z', '+00:00')),
                datetime.fromisoformat(subscription['current_period_end'].replace('Z', '+00:00'))
            )
            documents_remaining = max(0, documents_limit - usage)
        else:
            documents_remaining = None  # Unlimited
        
        # Check if subscription is active
        is_active = subscription['status'] == 'active'
        
        # Check expiration
        if subscription.get('current_period_end'):
            end_date = datetime.fromisoformat(subscription['current_period_end'].replace('Z', '+00:00'))
            now = datetime.now(end_date.tzinfo)
            if now > end_date:
                is_active = False
        
        return {
            "tier": tier,
            "documents_remaining": documents_remaining,
            "is_active": is_active,
            "expiry_date": subscription.get('current_period_end'),
            "organization_id": org['id'],
            "organization_name": org['name'],
            "role": org.get('organization_members', [{}])[0].get('role'),
            "seats_purchased": subscription.get('seats_purchased'),
            "seats_used": subscription.get('seats_used')
        }
    
    def has_access(self, user_id: str, feature_key: str) -> bool:
        """
        Check if user has access to a specific feature.
        """
        status = self.get_user_status(user_id)
        tier = status["tier"]
        is_active = status["is_active"]
        
        # If subscription is not active, no access to any features
        if not is_active:
            return False
        
        allowed_tiers = FEATURES.get(feature_key, [])
        return tier in allowed_tiers
    
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
            
            # Update organization tier
            update_query = """
            UPDATE organizations
            SET subscription_tier = %s
            WHERE id = %s
            """
            self.db.execute_query(update_query, (new_tier, org['id']))
            
            # Create or update subscription
            price_per_seat = PRICING[new_tier]['amount']
            
            existing_sub = self.org_manager.get_organization_subscription(org['id'])
            
            if existing_sub:
                # Update existing subscription
                update_sub_query = """
                UPDATE organization_subscriptions
                SET subscription_tier = %s,
                    seats_purchased = %s,
                    price_per_seat = %s,
                    status = 'active',
                    current_period_start = NOW(),
                    current_period_end = NOW() + INTERVAL '30 days',
                    next_billing_date = NOW() + INTERVAL '30 days',
                    updated_at = NOW()
                WHERE organization_id = %s
                """
                self.db.execute_query(
                    update_sub_query,
                    (new_tier, seats, price_per_seat, org['id'])
                )
            else:
                # Create new subscription
                self.db.create_organization_subscription(
                    organization_id=org['id'],
                    subscription_tier=new_tier,
                    seats_purchased=seats,
                    price_per_seat=price_per_seat
                )
            
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
        
        # Check if user is admin or owner
        role = org.get('organization_members', [{}])[0].get('role')
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
        
        # Check if user is admin or owner
        role = org.get('organization_members', [{}])[0].get('role')
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
