from app.core.database import SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash

def reset_passwords():
    db = SessionLocal()
    
    # Get all users
    users = db.query(User).all()
    
    print(f"Found {len(users)} users in the database")
    
    # Reset all passwords
    for user in users:
        print(f"\nProcessing user: {user.username} (ID: {user.id})")
        print(f"  Current status: {user.status}")
        print(f"  Current role: {user.role}")
        
        # Set a default password based on role
        if user.role == UserRole.SUPER_ADMIN:
            password = "Admin123!"
        else:
            password = "Password123!"
        
        # Ensure admin is active
        if user.username == "admin":
            user.status = UserStatus.ACTIVE
            user.role = UserRole.SUPER_ADMIN
            user.first_name = "Super"
            user.last_name = "Admin"
            print("  Updated admin user properties")
        
        # Update password
        user.hashed_password = get_password_hash(password)
        print(f"  Password reset to: {password}")
    
    # Commit changes
    db.commit()
    print("\nAll passwords have been reset")
    
    # Print summary
    print("\nUser summary after reset:")
    for user in users:
        print(f"  {user.username} ({user.role}): Status={user.status}")
        
    print("\nYou can now login with:")
    print("  Admin: username=admin, password=Admin123!")
    print("  Other users: password=Password123!")

if __name__ == "__main__":
    reset_passwords() 