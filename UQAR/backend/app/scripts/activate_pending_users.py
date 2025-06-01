from app.core.database import SessionLocal
from app.models.user import User, UserStatus
from sqlalchemy import text

def activate_pending_users():
    db = SessionLocal()
    
    # Get all pending users
    pending_users = db.query(User).filter(User.status == UserStatus.PENDING).all()
    
    if not pending_users:
        print("No pending users found in the database")
        return
    
    print(f"Found {len(pending_users)} pending users")
    
    # Ask for confirmation
    print("\nList of pending users:")
    for i, user in enumerate(pending_users, 1):
        print(f"  {i}. {user.username} ({user.email}) - {user.role}")
    
    print("\nActivating all pending users...")
    
    # Update all pending users to active
    query = text("""
    UPDATE users 
    SET status = 'ACTIVE'
    WHERE status = 'PENDING'
    """)
    
    # Execute the query
    result = db.execute(query)
    db.commit()
    
    # Check if the query affected any rows
    rows_affected = result.rowcount
    print(f"Rows affected: {rows_affected}")
    
    # Verify the update
    active_users = db.query(User).filter(User.status == UserStatus.ACTIVE).all()
    print(f"Active users after update: {len(active_users)}")
    
    print("\nAll users are now active and can login with these credentials:")
    for user in active_users:
        if user.username == "admin":
            print(f"  {user.username}: Admin123!")
        else:
            print(f"  {user.username}: Password123!")

if __name__ == "__main__":
    activate_pending_users() 