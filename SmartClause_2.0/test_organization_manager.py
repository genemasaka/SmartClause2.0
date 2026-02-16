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

from organization_manager import OrganizationManager
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
            # The actual method returns a dict merged with organization details or similar
            # Based on validation, it seems to trust get_user_organization return
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

if __name__ == "__main__":
    unittest.main()
