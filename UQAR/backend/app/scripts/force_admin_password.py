from app.core.database import SessionLocal
from app.models.user import User, UserRole, UserStatus
from sqlalchemy import text

def force_admin_password():
    db = SessionLocal()
    
    # Use a raw SQL update to ensure it works
    query = text("""
    UPDATE users 
    SET 
        hashed_password = '$argon2id$v=19$m=65536,t=3,p=1$uPFHfEkB6H8CuJ10YlZPYA$5ZI3Y6Yd22ziGg3YqSQb7eOxAFeqeOsXbLJ6GC2V/XU',
        role = 'SUPER_ADMIN',
        status = 'ACTIVE',
        first_name = 'Super',
        last_name = 'Admin'
    WHERE 
        username = 'admin'
    """)
    
    # Execute the query
    result = db.execute(query)
    db.commit()
    
    # Check if the query affected any rows
    rows_affected = result.rowcount
    print(f"Rows affected: {rows_affected}")
    
    # Get the admin user
    admin = db.query(User).filter(User.username == 'admin').first()
    
    if admin:
        print("Admin user found in database after update:")
        print(f"  ID: {admin.id}")
        print(f"  Username: {admin.username}")
        print(f"  Role: {admin.role}")
        print(f"  Status: {admin.status}")
        print(f"  Password hash: {admin.hashed_password[:30]}...")
        print("\nYou can now login with:")
        print("  Username: admin")
        print("  Password: Admin123!")
    else:
        print("Admin user not found after update!")

if __name__ == "__main__":
    force_admin_password() 