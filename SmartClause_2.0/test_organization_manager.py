"""
Unit tests for OrganizationManager
Verifies organization creation, member management, and seat checks
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from organization_manager import OrganizationManager, get_user_role_from_org
from database import DatabaseManager

class TestOrganizationManager(unittest.TestCase):
    
    def setUp(self):
        self.mock_db = MagicMock(spec=DatabaseManager)
        self.org_manager = OrganizationManager(self.mock_db)
        
    def test_create_individual_organization(self):
        """Test creating a new individual organization"""
        user_id = "user_123"
        user_email = "test@example.com"
        
        # Mock DB response - create_organization returns a list
        self.mock_db.create_organization.return_value = [{
            "id": "org_1",
            "name": "test",
            "subscription_tier": "trial"
        }]
        
        # Mock add_organization_member
        self.mock_db.add_organization_member.return_value = [{"id": "mem_1"}]
        
        result = self.org_manager.create_individual_organization(user_id, user_email)
        
        self.assertEqual(result["id"], "org_1")
        self.mock_db.create_organization.assert_called_once()
        
    def test_get_or_create_organization_existing(self):
        """Test retrieving existing organization for user"""
        user_id = "user_123"
        user_email = "test@example.com"
        
        # Mock DB finding existing org member
        self.mock_db.get_user_organization.return_value = {
            "organization_id": "org_1",
            "id": "org_1", 
            "name": "Existing Org"
        }
        
        org, created = self.org_manager.get_or_create_organization_for_user(user_id, user_email)
        
        self.assertFalse(created)
        self.assertEqual(org["id"], "org_1")
        
    def test_check_seat_availability_unlimited(self):
        """Test seat availability for Enterprise (unlimited)"""
        org_id = "org_1"
        
        # Mock Enterprise subscription
        self.mock_db.get_organization_subscription.return_value = {
            "subscription_tier": "enterprise",
            "seats_purchased": 100,
            "seats_used": 50,
            "status": "active"
        }
        
        result = self.org_manager.check_seat_availability(org_id)
        
        self.assertTrue(result["can_add_members"])
        self.assertEqual(result["seats_available"], 50)
        
    def test_check_seat_availability_full(self):
        """Test seat availability when full"""
        org_id = "org_1"
        
        # Mock Team subscription full
        self.mock_db.get_organization_subscription.return_value = {
            "subscription_tier": "team",
            "seats_purchased": 5,
            "seats_used": 5,
            "status": "active"
        }
        
        result = self.org_manager.check_seat_availability(org_id)
        
        self.assertFalse(result["can_add_members"])
        self.assertEqual(result["seats_available"], 0)

    # ── Issue 2: Domain auto-join security ────────────────────────────────────

    def test_domain_autojoin_blocked_when_flag_off(self):
        """
        Issue 2: A new user with a corporate email matching an existing org should
        NOT be auto-added as a member when allow_domain_autojoin is False (the default).
        """
        user_id = "attacker_user"
        user_email = "attacker@targetfirm.com"

        # User is not already in any org
        self.mock_db.get_user_organization.return_value = None

        # An org exists for this domain, but auto-join is explicitly disabled
        self.mock_db.get_organization_by_domain.return_value = {
            "id": "org_target",
            "name": "Target Firm",
            "allow_domain_autojoin": False,
        }

        # Creating a new individual org for the user (fallback path)
        self.mock_db.create_organization.return_value = [{
            "id": "org_new",
            "name": "attacker",
            "subscription_tier": "trial",
        }]
        self.mock_db.add_organization_member.return_value = [{"id": "mem_new"}]

        org, created = self.org_manager.get_or_create_organization_for_user(
            user_id, user_email
        )

        # Should have created a new personal org, NOT joined the existing one
        self.assertTrue(created)
        self.assertEqual(org["id"], "org_new")

        # add_organization_member must only be called once — for the new personal org,
        # never for the existing target org
        call_args_list = self.mock_db.add_organization_member.call_args_list
        for call in call_args_list:
            self.assertNotEqual(
                call.kwargs.get("organization_id") or (call.args[0] if call.args else None),
                "org_target",
                "User was auto-joined to target org despite allow_domain_autojoin=False",
            )

    def test_domain_autojoin_allowed_when_flag_on(self):
        """
        Issue 2: A new user with a matching corporate email SHOULD be auto-added
        when the org admin has explicitly enabled allow_domain_autojoin=True.
        """
        user_id = "legit_user"
        user_email = "newbie@firm.com"

        # User is not already in any org
        self.mock_db.get_user_organization.return_value = None

        # Org exists and auto-join is enabled by the admin
        self.mock_db.get_organization_by_domain.return_value = {
            "id": "org_firm",
            "name": "The Firm",
            "allow_domain_autojoin": True,
        }
        self.mock_db.add_organization_member_atomic.return_value = {
            "success": True, "member": {"id": "mem_new", "user_id": user_id, "role": "member"}
        }
        self.mock_db.get_organization_subscription.return_value = {
            "seats_purchased": 10,
            "seats_used": 3,
        }

        org, created = self.org_manager.get_or_create_organization_for_user(
            user_id, user_email
        )

        # Should have returned the existing org (not created a new one)
        self.assertFalse(created)
        self.assertEqual(org["id"], "org_firm")

        # add_organization_member_atomic must have been called for the existing org
        self.mock_db.add_organization_member_atomic.assert_called_once_with(
            organization_id="org_firm",
            user_id=user_id,
            role="member",
            invited_by=None,
        )

    # ── Issue 5: Role extraction correctness ─────────────────────────────────

    def test_get_user_role_from_org_correct_user(self):
        """
        Issue 5: get_user_role_from_org must return the role for the *specified*
        user_id, not blindly take index 0. An admin listed first must not cause a
        regular member further down the list to receive admin privileges.
        """
        org = {
            "id": "org_1",
            "organization_members": [
                {"user_id": "admin_user", "role": "admin"},   # index 0 — admin
                {"user_id": "regular_user", "role": "member"}, # index 1 — member
                {"user_id": "owner_user", "role": "owner"},    # index 2 — owner
            ]
        }

        # Regular member must not receive 'admin' even though admin is at index 0
        self.assertEqual(get_user_role_from_org(org, "regular_user"), "member")

        # Owner lookup should work regardless of position
        self.assertEqual(get_user_role_from_org(org, "owner_user"), "owner")

        # Admin lookup should work too
        self.assertEqual(get_user_role_from_org(org, "admin_user"), "admin")

    def test_get_user_role_from_org_unknown_user_defaults_to_member(self):
        """
        Issue 5: If the user_id isn't present in the members list (e.g. the query
        didn't join their row), fall back to 'member' rather than crashing.
        """
        org = {
            "id": "org_1",
            "organization_members": [
                {"user_id": "some_other_user", "role": "admin"},
            ]
        }

        # Unknown user should default to 'member', not raise an exception
        result = get_user_role_from_org(org, "ghost_user")
        self.assertEqual(result, "member")


if __name__ == "__main__":
    unittest.main()
