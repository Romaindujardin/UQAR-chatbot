from app.core.database import SessionLocal
from app.models.user import User, UserRole, UserStatus
from sqlalchemy import text

def create_simple_admin():
    db = SessionLocal()
    
    # Use a raw SQL query to create a simple admin user
    query = text("""
    INSERT INTO users (
        username, 
        email, 
        hashed_password, 
        first_name, 
        last_name, 
        role, 
        status
    ) 
    VALUES (
        'admin2', 
        'admin2@uqar.ca', 
        'adminpass', 
        'Test', 
        'Admin', 
        'SUPER_ADMIN', 
        'ACTIVE'
    )
    ON CONFLICT (username) DO UPDATE 
    SET 
        hashed_password = 'adminpass',
        status = 'ACTIVE',
        role = 'SUPER_ADMIN'
    """)
    
    try:
        # Execute the query
        result = db.execute(query)
        db.commit()
        print("Simple admin user created or updated")
        
        # Print the login info
        print("\nYou can now login with:")
        print("  Username: admin2")
        print("  Password: adminpass")
        
        # Update the verify_password function
        print("\nIMPORTANT: The backend now accepts plaintext passwords for testing.")
        print("This is ONLY for development purposes.")
    except Exception as e:
        print(f"Error creating simple admin: {str(e)}")
        db.rollback()

if __name__ == "__main__":
    create_simple_admin() 