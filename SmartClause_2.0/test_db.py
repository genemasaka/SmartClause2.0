# test_db.py
from database import DatabaseManager

db = DatabaseManager()
db.set_user("test-user-id")  # Temporary for testing
print("✅ Database connected successfully!")