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
        
        # Check and add new columns to candidate_reference_check table
        print("\nChecking candidate_reference_check table...")
        
        # List of new columns to add
        new_columns = [
            ("reference_phone", "VARCHAR(20) NULL"),
            ("reference_designation", "VARCHAR(100) NULL"),
            ("candidate_doj", "VARCHAR(20) NULL"),
            ("candidate_lwd", "VARCHAR(20) NULL"),
            ("candidate_leaving_reason", "TEXT NULL"),
            ("candidate_strengths", "TEXT NULL"),
            ("candidate_improvements", "TEXT NULL"),
            ("comments", "TEXT NULL"),
            ("last_ctc", "VARCHAR(50) NULL"),
            ("rehire", "BOOLEAN DEFAULT FALSE")
        ]
        
        for column_name, column_type in new_columns:
            result = connection.execute(text(f"""
                SELECT COUNT(*) as count 
                FROM information_schema.columns 
                WHERE table_schema = 'hrms_db' 
                AND table_name = 'candidate_reference_check' 
                AND column_name = '{column_name}'
            """))
            
            if result.fetchone()[0] == 0:
                print(f"Adding {column_name} column to candidate_reference_check table...")
                try:
                    connection.execute(text(f"ALTER TABLE candidate_reference_check ADD COLUMN {column_name} {column_type}"))
                    connection.commit()
                    print(f"✓ {column_name} column added successfully")
                except Exception as e:
                    print(f"⚠️ Error adding {column_name}: {e}")
            else:
                print(f"✓ {column_name} column already exists")
        
        print("\n🎉 Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database() 