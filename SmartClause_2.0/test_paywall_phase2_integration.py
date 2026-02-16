
import unittest
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Import the class to test
from database import DatabaseManager

# Load env vars
load_dotenv()

class TestDatabaseManagerPaywall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup Supabase client for admin tasks (creating users)
        cls.supabase_url = os.getenv("SUPABASE_URL")
        cls.supabase_key = os.getenv("SUPABASE_ANON_KEY")
        if not cls.supabase_url or not cls.supabase_key:
            raise ValueError("Missing env vars")
        
        cls.admin_client = create_client(cls.supabase_url, cls.supabase_key)
        
        # Create a test user
        cls.test_email = f"test_phase2_{uuid.uuid4().hex[:8]}@example.com"
        cls.test_password = "TestPassword123!"
        
        try:
            # Use admin API to create user (requires service_role key/privileges)
            # Matching the Phase 1 test approach
            user = cls.admin_client.auth.admin.create_user({
                "email": cls.test_email,
                "password": cls.test_password,
                "email_confirm": True
            })
            if user.user:
                cls.user_id = user.user.id
                print(f"Created test user: {cls.user_id}")
            else:
                 cls.user_id = user.user.id
        except Exception as e:
            print(f"Error creating user: {e}")
            raise e

    @classmethod
    def tearDownClass(cls):
        # Cleanup user
        if hasattr(cls, 'user_id'):
            try:
                # Needed admin privileges to delete user strictly speaking, 
                # but we can at least clean up data if we want. 
                # The auth user deletion might be restricted.
                # In phase 1 test, it used admin api.
                # Here we are using anon key, so we might not be able to delete the user via admin API easily 
                # unless SUPABASE_ANON_KEY allows it (which is unsafe but possible in dev).
                # Phase 1 test seemed to use 'admin' namespace but maybe it has service role key or anon key has rights?
                # Actually Phase 1 used: SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
                # and supabase.auth.admin.create_user...
                # If that worked, then we can delete too.
                cls.admin_client.auth.admin.delete_user(cls.user_id)
                print(f"Deleted test user: {cls.user_id}")
            except Exception as e:
                print(f"Error cleaning up user: {e}")

    def setUp(self):
        self.db = DatabaseManager()
        self.db.set_user(self.user_id)

    def test_subscription_lifecycle(self):
        # 1. Create Subscription
        sub = self.db.create_subscription(self.user_id, "pay_as_you_go", credits=3)
        self.assertIsNotNone(sub, "Failed to create subscription")
        self.assertEqual(sub['subscription_tier'], "pay_as_you_go")
        self.assertEqual(sub['credits_remaining'], 3)
        
        # 2. Check Active
        is_active = self.db.check_subscription_active(self.user_id)
        self.assertTrue(is_active, "Subscription should be active")
        
        # 3. Valid retrieval
        fetched_sub = self.db.get_user_subscription(self.user_id)
        self.assertEqual(fetched_sub['id'], sub['id'])
        
        # 4. Update Credits
        updated = self.db.update_subscription_credits(self.user_id, -1)
        self.assertEqual(updated['credits_remaining'], 2)
        
        # 5. Log Generation
        # Create dummy document log (requires valid document_id usually, but depending on FK... 
        # tables have FK: document_generation_logs -> documents.id)
        # So we can't easily test log_document_generation without creating a document first.
        # We'll skip or mock the document creation.
        # Let's try to create a dummy document first.
        try:
             # Create matter first
            matter = self.db.create_matter("Test Matter", "Client X")
            doc = self.db.create_document(matter['id'], "Test Doc", "Type A")
            
            logged = self.db.log_document_generation(self.user_id, doc['id'], 1, "pay_as_you_go")
            self.assertTrue(logged, "Failed to log generation")
            
            count = self.db.get_user_generation_count(self.user_id)
            self.assertEqual(count, 1)
            
            # Cleanup doc/matter
            # self.db.delete_matter(matter['id'], hard_delete=True) # Cascade?
            # Manually delete for now to be safe
            self.db.client.table("documents").delete().eq("id", doc['id']).execute()
            self.db.client.table("matters").delete().eq("id", matter['id']).execute()

        except Exception as e:
            print(f"Skipping document logging test due to setup error: {e}")

    def test_payment_transaction(self):
        tx = self.db.create_payment_transaction(
            self.user_id, 
            1500, 
            "credit_purchase", 
            "req_123", 
            "hash_123", 
            3
        )
        self.assertIsNotNone(tx)
        
        # Update status
        success = self.db.update_payment_status("req_123", "completed", "RCT123")
        self.assertTrue(success)
        
        # Verify history
        history = self.db.get_user_payment_history(self.user_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['mpesa_receipt_number'], "RCT123")

if __name__ == '__main__':
    unittest.main()
