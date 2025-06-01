import sys
sys.path.append(".")

from app.core.database import SessionLocal
from app.models.user import User, UserStatus

def activate_pending_users():
    db = SessionLocal()
    
    # Get all pending users
    pending_users = db.query(User).filter(User.status == UserStatus.PENDING).all()
    
    print(f"Found {len(pending_users)} pending users")
    
    if not pending_users:
        print("No pending users found.")
        return
    
    # Activate all pending users
    for user in pending_users:
        print(f"Activating user: {user.username} ({user.email})")
        user.status = UserStatus.ACTIVE
    
    # Commit changes
    db.commit()
    print("All pending users have been activated.")

if __name__ == "__main__":
    activate_pending_users() 