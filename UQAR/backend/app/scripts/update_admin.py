from app.core.database import SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash

def update_admin():
    db = SessionLocal()
    
    # Find admin user
    admin = db.query(User).filter(User.username == "admin").first()
    
    if not admin:
        print("Admin user not found. Creating new admin user...")
        
        # Create new admin user
        hashed_password = get_password_hash("Admin123!")
        
        new_admin = User(
            username="admin",
            email="admin@uqar.ca",
            hashed_password=hashed_password,
            first_name="Super",
            last_name="Admin",
            role=UserRole.SUPER_ADMIN,
            status=UserStatus.ACTIVE
        )
        
        db.add(new_admin)
        db.commit()
        print("New admin user created.")
        admin = new_admin
    else:
        print(f"Found admin user with ID: {admin.id}")
        
        # Update admin user
        admin.username = "admin"
        admin.email = "admin@uqar.ca"
        admin.first_name = "Super" 
        admin.last_name = "Admin"
        admin.role = UserRole.SUPER_ADMIN
        admin.status = UserStatus.ACTIVE
        
        # Update password
        admin.hashed_password = get_password_hash("Admin123!")
        
        db.commit()
        print("Admin user updated with new password.")
    
    print("Admin user details:")
    print(f"  Username: {admin.username}")
    print(f"  Role: {admin.role}")
    print(f"  Status: {admin.status}")
    print(f"  Full name: {admin.full_name}")
    print("Password set to: Admin123!")

if __name__ == "__main__":
    update_admin() 