import sys
sys.path.append(".")

from app.core.database import SessionLocal
from app.models.user import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_admin():
    db = SessionLocal()
    
    # Check for admin user
    admin = db.query(User).filter(User.username == "admin").first()
    
    if admin:
        print("Admin user exists with the following details:")
        print(f"Username: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role}")
        print(f"Status: {admin.status}")
        print(f"First Name: {admin.first_name}")
        print(f"Last Name: {admin.last_name}")
        print("Note: The password is not shown for security reasons, but from create_admin.py it should be: Admin123!")
    else:
        print("Admin user does not exist.")
    
    db.close()

if __name__ == "__main__":
    check_admin() 