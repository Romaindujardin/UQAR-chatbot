import sys
sys.path.append(".")

from app.core.database import SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash
from sqlalchemy import func

def create_admin():
    db = SessionLocal()
    
    # Check if admin already exists
    admin = db.query(User).filter(User.username == "admin").first()
    
    if admin:
        print(f"Admin user already exists with status: {admin.status}")
        
        # Ensure admin is active
        if admin.status != UserStatus.ACTIVE:
            admin.status = UserStatus.ACTIVE
            db.commit()
            print("Admin status updated to ACTIVE")
        
        return
    
    # Create admin user
    hashed_password = get_password_hash("Admin123!")
    
    admin_user = User(
        username="admin",
        email="admin@uqar.ca",
        hashed_password=hashed_password,
        first_name="Admin",
        last_name="UQAR",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        created_at=func.now()
    )
    
    db.add(admin_user)
    db.commit()
    
    print("Admin user created successfully:")
    print(f"Username: admin")
    print(f"Password: Admin123!")
    print(f"Role: {admin_user.role}")
    print(f"Status: {admin_user.status}")

if __name__ == "__main__":
    create_admin() 