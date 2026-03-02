
import os
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

user_id = "1a27aeea-a4dd-48ba-b17e-695b9fb7c0c6"

def test_query():
    result = supabase.table("organizations")\
        .select("*, organization_members!inner(user_id, role, status)")\
        .eq("organization_members.user_id", user_id)\
        .eq("organization_members.status", "active")\
        .single()\
        .execute()
    
    print(json.dumps(result.data, indent=2))

if __name__ == "__main__":
    test_query()
