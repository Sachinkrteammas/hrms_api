# migrate_db.py
# Database migration script to add missing columns

from sqlalchemy import text
from database import engine

def migrate_database():
    """Add missing columns to existing tables"""
    
    with engine.connect() as connection:
        # Check if is_admin column exists in users table
        result = connection.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_schema = 'hrms_db' 
            AND table_name = 'users' 
            AND column_name = 'is_admin'
        """))
        
        if result.fetchone()[0] == 0:
            print("Adding is_admin column to users table...")
            connection.execute(text("ALTER TABLE users ADD COLUMN is_admin VARCHAR(1) DEFAULT 'N'"))
            connection.commit()
            print("✓ is_admin column added successfully")
        else:
            print("✓ is_admin column already exists")
        
        # Check if company_id column exists in users table
        result = connection.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_schema = 'hrms_db' 
            AND table_name = 'users' 
            AND column_name = 'company_id'
        """))
        
        if result.fetchone()[0] == 0:
            print("Adding company_id column to users table...")
            connection.execute(text("ALTER TABLE users ADD COLUMN company_id INT NULL"))
            connection.commit()
            print("✓ company_id column added successfully")
        else:
            print("✓ company_id column already exists")
        
        # Check if credits column exists in company table
        result = connection.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_schema = 'hrms_db' 
            AND table_name = 'company' 
            AND column_name = 'credits'
        """))
        
        if result.fetchone()[0] == 0:
            print("Adding credits column to company table...")
            connection.execute(text("ALTER TABLE company ADD COLUMN credits INT DEFAULT 0"))
            connection.commit()
            print("✓ credits column added successfully")
        else:
            print("✓ credits column already exists")
        
        # Check if candidates table exists
        result = connection.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = 'hrms_db' 
            AND table_name = 'candidates'
        """))
        
        if result.fetchone()[0] == 0:
            print("Creating candidates table...")
            connection.execute(text("""
                CREATE TABLE candidates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    company_id INT,
                    status VARCHAR(50) DEFAULT 'PENDING',
                    FOREIGN KEY (company_id) REFERENCES company(id)
                )
            """))
            connection.commit()
            print("✓ candidates table created successfully")
        else:
            print("✓ candidates table already exists")
        
        print("\n🎉 Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database() 