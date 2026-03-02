
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")

if not url or not key:
    print("Missing Supabase credentials in .env")
    exit(1)

supabase = create_client(url, key)

def list_members():
    print("--- Organizations ---")
    orgs = supabase.table("organizations").select("*").execute()
    for org in orgs.data:
        print(f"ID: {org['id']}, Name: {org['name']}, Tier: {org['subscription_tier']}")
        
    print("\n--- Organization Members ---")
    members = supabase.table("organization_members").select("*").execute()
    for member in members.data:
        # Try to get user email from auth.users (requires service role key which we have)
        # However, supabase-py doesn't easily expose auth.users. 
        # We can look at the user_id and then look at the email in auth.
        user_id = member['user_id']
        print(f"OrgID: {member['organization_id']}, UserID: {user_id}, Role: {member['role']}, Status: {member['status']}")

if __name__ == "__main__":
    list_members()
