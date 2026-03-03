"""
Organization Manager - Enterprise Subscription Management
Handles organization creation, member management, and subscription enforcement
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
import re


class SubscriptionTier(Enum):
    TRIAL = "trial"
    INDIVIDUAL = "individual"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class MemberRole(Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


def get_user_role_from_org(org: dict, user_id: str) -> str:
    """
    Safely extract the role for a specific user from the joined
    'organization_members' list on the org dict.

    This replaces the fragile `org.get('organization_members', [{}])[0].get('role')`
    pattern used previously, which silently returned the wrong role whenever
    the member list was ordered differently or had multiple entries.

    Args:
        org: Organization dict with an embedded 'organization_members' list
        user_id: The user whose role we want to look up

    Returns:
        Role string ('owner', 'admin', 'member') or 'member' as safe default
    """
    members = org.get('organization_members') or []
    for m in members:
        if m.get('user_id') == user_id:
            return m.get('role', 'member')
    return 'member'


class OrganizationManager:
    """Manages organization-level operations for enterprise subscriptions"""
    
    def __init__(self, db_manager):
        """
        Initialize OrganizationManager
        
        Args:
            db_manager: Database manager instance for executing queries
        """
        self.db = db_manager
        self.FREE_EMAIL_PROVIDERS = [
            'gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com',
            'aol.com', 'icloud.com', 'protonmail.com', 'mail.com'
        ]
    
    def extract_email_domain(self, email: str) -> Optional[str]:
        """
        Extract domain from email, excluding free providers
        
        Args:
            email: User's email address
            
        Returns:
            Domain string if corporate email, None if free provider
        """
        try:
            domain = email.split('@')[1].lower()
            return None if domain in self.FREE_EMAIL_PROVIDERS else domain
        except (IndexError, AttributeError):
            return None
    
    def create_individual_organization(
        self, 
        user_id: str, 
        user_email: str,
        user_name: Optional[str] = None
    ) -> Dict:
        """
        Create an individual organization (for solo practitioners)
        
        Args:
            user_id: User's UUID
            user_email: User's email
            user_name: User's full name (optional)
            
        Returns:
            Dict with organization details
        """
        org_name = user_name or user_email.split('@')[0]
        
        org = self.db.create_organization(
            name=org_name,
            email_domain=None,
            admin_user_id=user_id,
            subscription_tier=SubscriptionTier.TRIAL.value,
            billing_email=user_email
        )
        
        if org:
            # Add user as owner
            self.add_organization_member(org[0]['id'], user_id, MemberRole.OWNER.value)
            return org[0]
        
        return None
    
    def create_team_organization(
        self,
        name: str,
        email_domain: str,
        admin_user_id: str,
        billing_email: str,
        seats_purchased: int = 3
    ) -> Dict:
        """
        Create a team organization (for law firms)
        
        Args:
            name: Organization name
            email_domain: Email domain for auto-joining
            admin_user_id: Owner's user ID
            billing_email: Billing contact email
            seats_purchased: Number of seats to purchase (min 3)
            
        Returns:
            Dict with organization and subscription details
        """
        if seats_purchased < 3:
            raise ValueError("Team tier requires minimum 3 seats")
        
        # Create organization
        org_result = self.db.create_organization(
            name=name,
            email_domain=email_domain,
            admin_user_id=admin_user_id,
            subscription_tier=SubscriptionTier.TEAM.value,
            billing_email=billing_email
        )
        
        if not org_result:
            raise Exception("Failed to create organization")
        
        org = org_result[0]
        
        # Create subscription
        sub_result = self.db.create_organization_subscription(
            organization_id=org['id'],
            subscription_tier=SubscriptionTier.TEAM.value,
            seats_purchased=seats_purchased,
            price_per_seat=650000  # KSh 6,500 in minor units
        )
        
        # Add owner as member
        self.add_organization_member(org['id'], admin_user_id, MemberRole.OWNER.value)
        
        return {
            'organization': org,
            'subscription': sub_result[0] if sub_result else None
        }
    
    def get_or_create_organization_for_user(
        self,
        user_id: str,
        user_email: str,
        user_name: Optional[str] = None
    ) -> Tuple[Dict, bool]:
        """
        Get existing organization or create new one based on email domain
        
        Args:
            user_id: User's UUID
            user_email: User's email
            user_name: User's full name (optional)
            
        Returns:
            Tuple of (organization dict, was_created bool)
        """
        domain = self.extract_email_domain(user_email)
        
        # Check if user is already in an organization
        existing_org = self.get_user_organization(user_id)
        if existing_org:
            return existing_org, False
        
        # If corporate email, check for existing organization with that domain.
        # SECURITY: Auto-join is an opt-in feature that org admins must explicitly
        # enable (allow_domain_autojoin = True on the org record). Without it,
        # any user who registers with a matching corporate email would be silently
        # added to that firm's org — a significant unauthorized-access risk.
        if domain:
            org = self.get_organization_by_domain(domain)
            if org and org.get('allow_domain_autojoin', False):
                # Admin has explicitly enabled domain-based auto-joining
                self.add_organization_member(org['id'], user_id, MemberRole.MEMBER.value)
                return org, False
        
        # Create new individual organization
        org = self.create_individual_organization(user_id, user_email, user_name)
        return org, True
    
    def get_organization_by_domain(self, email_domain: str) -> Optional[Dict]:
        """
        Find organization by email domain
        
        Args:
            email_domain: Domain to search for
            
        Returns:
            Organization dict or None
        """
        return self.db.get_organization_by_domain(email_domain)
    
    def get_user_organization(self, user_id: str) -> Optional[Dict]:
        """
        Get user's organization
        
        Args:
            user_id: User's UUID
            
        Returns:
            Organization dict or None
        """
        return self.db.get_user_organization(user_id)
    
    def add_organization_member(
        self,
        organization_id: str,
        user_id: str,
        role: str = 'member',
        invited_by: Optional[str] = None
    ) -> Dict:
        """
        Add member to organization
        
        Args:
            organization_id: Organization UUID
            user_id: User UUID to add
            role: Member role (owner, admin, member)
            invited_by: UUID of user who invited (optional)
            
        Returns:
            Member record dict
        """
        # Use the atomic RPC that acquires a row-level lock on the subscription
        # before inserting, preventing race conditions on seat enforcement.
        response = self.db.add_organization_member_atomic(
            organization_id=organization_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by
        )

        if not response.get('success'):
            error_msg = response.get('error', 'Unknown error adding member')
            raise ValueError(error_msg)

        # The atomic function also updates seats_used, so no separate call needed.
        return response.get('member')
    
    def remove_organization_member(
        self,
        organization_id: str,
        user_id: str
    ) -> bool:
        """
        Remove member from organization (soft delete)
        
        Args:
            organization_id: Organization UUID
            user_id: User UUID to remove
            
        Returns:
            True if successful
        """
        # Prevent removing the owner
        members = self.db.get_organization_members(organization_id, include_suspended=False)
        
        for member in members:
            if member['user_id'] == user_id and member['role'] == 'owner':
                raise ValueError("Cannot remove organization owner")
        
        # Update member status
        query = """
        UPDATE organization_members
        SET status = 'suspended'
        WHERE organization_id = %s AND user_id = %s
        RETURNING id
        """
        
        result = self.db.execute_query(query, (organization_id, user_id))
        
        # Update seats_used count
        self._update_seats_used(organization_id)
        
        return bool(result)
    
    def get_organization_members(
        self,
        organization_id: str,
        include_suspended: bool = False
    ) -> List[Dict]:
        """
        Get all members of an organization
        
        Args:
            organization_id: Organization UUID
            include_suspended: Include suspended members
            
        Returns:
            List of member dicts with user info
        """
        return self.db.get_organization_members(organization_id, include_suspended)
    
    def update_member_role(
        self,
        organization_id: str,
        user_id: str,
        new_role: str
    ) -> bool:
        """
        Update member's role
        
        Args:
            organization_id: Organization UUID
            user_id: User UUID
            new_role: New role (admin, member)
            
        Returns:
            True if successful
        """
        if new_role not in ['admin', 'member']:
            raise ValueError("Role must be 'admin' or 'member'")
        
        query = """
        UPDATE organization_members
        SET role = %s
        WHERE organization_id = %s AND user_id = %s AND role != 'owner'
        RETURNING id
        """
        
        result = self.db.execute_query(query, (new_role, organization_id, user_id))
        return bool(result)
    
    def get_organization_subscription(self, organization_id: str) -> Optional[Dict]:
        """
        Get organization's subscription details
        
        Args:
            organization_id: Organization UUID
            
        Returns:
            Subscription dict or None
        """
        return self.db.get_organization_subscription(organization_id)
    
    def check_seat_availability(self, organization_id: str) -> Dict:
        """
        Check if organization has available seats
        
        Args:
            organization_id: Organization UUID
            
        Returns:
            Dict with seats_purchased, seats_used, seats_available
        """
        subscription = self.get_organization_subscription(organization_id)
        
        if not subscription:
            return {'seats_purchased': 0, 'seats_used': 0, 'seats_available': 0}
        
        seats_available = subscription['seats_purchased'] - subscription['seats_used']
        
        return {
            'seats_purchased': subscription['seats_purchased'],
            'seats_used': subscription['seats_used'],
            'seats_available': seats_available,
            'can_add_members': seats_available > 0
        }
    
    def add_seats(
        self,
        organization_id: str,
        additional_seats: int
    ) -> Dict:
        """
        Add seats to organization subscription
        
        Args:
            organization_id: Organization UUID
            additional_seats: Number of seats to add
            
        Returns:
            Updated subscription dict
        """
        if additional_seats < 1:
            raise ValueError("Must add at least 1 seat")
        
        query = """
        UPDATE organization_subscriptions
        SET seats_purchased = seats_purchased + %s,
            updated_at = NOW()
        WHERE organization_id = %s
        RETURNING id, seats_purchased, seats_used, price_per_seat
        """
        
        result = self.db.execute_query(query, (additional_seats, organization_id))
        return result[0] if result else None
    
    def _update_seats_used(self, organization_id: str) -> None:
        """
        Update the seats_used count based on active members
        
        Args:
            organization_id: Organization UUID
        """
        query = """
        UPDATE organization_subscriptions
        SET seats_used = (
            SELECT COUNT(*) 
            FROM organization_members 
            WHERE organization_id = %s AND status = 'active'
        )
        WHERE organization_id = %s
        """
        
        self.db.execute_query(query, (organization_id, organization_id))
    
    def get_organization_usage_summary(
        self,
        organization_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Dict:
        """
        Get organization-wide usage statistics
        
        Args:
            organization_id: Organization UUID
            period_start: Start of period (defaults to current billing period)
            period_end: End of period (defaults to current billing period)
            
        Returns:
            Dict with usage statistics
        """
        # Get subscription to determine billing period
        subscription = self.get_organization_subscription(organization_id)
        
        if not subscription:
            return {'total_documents': 0, 'documents_by_user': []}
        
        if not period_start:
            period_start = subscription['current_period_start']
        if not period_end:
            period_end = subscription['current_period_end']
        
        try:
            supabase = self.db.supabase

            # Query 1: total document count for the org in the period
            total_result = (
                supabase.table("document_usage")
                .select("id", count="exact")
                .eq("organization_id", organization_id)
                .gte("created_at", str(period_start))
                .lt("created_at", str(period_end))
                .execute()
            )
            total_documents = total_result.count or 0

            # Query 2: per-user breakdown — fetch user_ids, aggregate in Python,
            # then enrich with member info (avoids the auth.users JOIN)
            usage_result = (
                supabase.table("document_usage")
                .select("user_id")
                .eq("organization_id", organization_id)
                .gte("created_at", str(period_start))
                .lt("created_at", str(period_end))
                .execute()
            )
            user_counts: dict = {}
            for row in (usage_result.data or []):
                uid = row.get("user_id")
                if uid:
                    user_counts[uid] = user_counts.get(uid, 0) + 1

            # Get member details to map user_id → email / name
            members = self.db.get_organization_members(organization_id)
            member_map = {m["user_id"]: m for m in (members or [])}

            documents_by_user = []
            for uid, count in sorted(user_counts.items(), key=lambda x: -x[1]):
                member = member_map.get(uid, {})
                documents_by_user.append({
                    "email": member.get("email", uid),
                    "full_name": (member.get("full_name")
                                  or member.get("name", "")),
                    "documents_created": count,
                })

        except Exception as _exc:
            import logging
            logging.getLogger(__name__).warning(
                f"get_organization_usage_summary: Supabase query failed — {_exc}"
            )
            total_documents = 0
            documents_by_user = []

        return {
            'total_documents': total_documents,
            'documents_by_user': documents_by_user,
            'period_start': period_start,
            'period_end': period_end,
            'subscription_tier': subscription['subscription_tier']
        }
    
    def can_create_document(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if user can create a document based on their subscription limits
        
        Args:
            user_id: User's UUID
            
        Returns:
            Tuple of (can_create: bool, reason: str)
        """
        from subscription_manager import PRICING
        from datetime import datetime
        
        # Get user's organization
        org = self.get_user_organization(user_id)
        
        if not org:
            return False, "No active organization found"
        
        # Get subscription tier from organization
        tier = org.get('subscription_tier', SubscriptionTier.TRIAL.value)
        
        # Get subscription if exists (for paid tiers)
        subscription = self.get_organization_subscription(org['id'])
        
        # Get tier config
        tier_config = PRICING.get(tier, {})
        
        # Check trial period expiration for trial users
        if tier == SubscriptionTier.TRIAL.value:
            # Trial users get unlimited documents for 14 days
            if org.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(org['created_at'].replace('Z', '+00:00'))
                    trial_days = tier_config.get('trial_days', 14)
                    trial_end = created_at + timedelta(days=trial_days)
                    now = datetime.now(created_at.tzinfo)
                    
                    if now > trial_end:
                        return False, f"Trial period expired. Please upgrade to continue."
                    
                    # Within trial period - unlimited documents
                    days_left = (trial_end - now).days + 1
                    return True, f"Trial: {days_left} days remaining (unlimited documents)"
                except:
                    # If date parsing fails, allow but warn
                    return True, "Trial: unlimited documents"
            else:
                # No created_at, allow with warning
                return True, "Trial: unlimited documents"
        
        # For paid tiers, check subscription
        if not subscription:
            return False, "No active subscription. Please subscribe to continue."
        
        if subscription['status'] != 'active':
            return False, f"Subscription is {subscription['status']}. Please renew."
        
        # Check if subscription period has expired
        if subscription.get('current_period_end'):
            try:
                end_date = datetime.fromisoformat(subscription['current_period_end'].replace('Z', '+00:00'))
                now = datetime.now(end_date.tzinfo)
                if now > end_date:
                    return False, "Subscription period expired. Please renew."
            except:
                pass  # Continue if date parsing fails
        
        # Check document limits
        documents_per_month = tier_config.get('documents_per_month')
        
        # If unlimited documents (None for Enterprise or Trial)
        if documents_per_month is None:
            return True, "Unlimited documents"
        
        # Check user's usage for current period
        period_start = subscription.get('current_period_start')
        period_end = subscription.get('current_period_end')
        
        if not period_start or not period_end:
            # No period defined, allow
            return True, "Active subscription"
        
        documents_used = self.db.get_user_document_usage(
            user_id,
            period_start,
            period_end
        )
        
        if documents_used >= documents_per_month:
            return False, f"Monthly limit reached ({documents_used}/{documents_per_month})"
        
        return True, f"Usage: {documents_used}/{documents_per_month}"
    
    def record_document_creation(
        self,
        user_id: str,
        document_type: str = 'general'
    ) -> bool:
        """
        Record that a user created a document.

        For trial users (no subscription record) this is a no-op that returns True,
        so document generation is never blocked by a missing usage record.

        Args:
            user_id: User's UUID
            document_type: Type of document created

        Returns:
            True if recorded successfully (or skipped for trial)
        """
        import logging
        _logger = logging.getLogger(__name__)

        try:
            org = self.get_user_organization(user_id)

            if not org:
                # No org yet (new user in onboarding) — don't block document creation
                _logger.warning(
                    f"record_document_creation: no org for user {user_id} — skipping usage record"
                )
                return True

            subscription = self.get_organization_subscription(org['id'])

            if not subscription:
                # Trial user: no paid subscription — skip usage recording silently
                _logger.info(
                    f"record_document_creation: no subscription for org {org['id']} "
                    f"(trial user {user_id}) — skipping usage record"
                )
                return True

            result = self.db.record_document_usage(
                user_id=user_id,
                organization_id=org['id'],
                document_type=document_type,
                billing_period_start=subscription['current_period_start'],
                billing_period_end=subscription['current_period_end']
            )
            return bool(result)

        except Exception as e:
            _logger.error(f"record_document_creation failed for user {user_id}: {e}")
            # Don't block document creation due to a recording failure
            return True
