#!/usr/bin/env python3
"""
Simple script to add missing columns to candidate_reference_check table
Run this with: python add_columns.py
"""

import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_missing_columns():
    """Add missing columns to candidate_reference_check table"""
    
    # Database connection details
    db_host = "localhost"
    db_user = "hrms_user"
    db_password = "your_password"  # Update this with your actual password
    db_name = "hrms_db"
    
    try:
        # Connect to database
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # List of columns to add
        columns_to_add = [
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
        
        print("Checking and adding missing columns...")
        
        for column_name, column_type in columns_to_add:
            # Check if column exists
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_schema = '{db_name}' 
                AND table_name = 'candidate_reference_check' 
                AND column_name = '{column_name}'
            """)
            
            exists = cursor.fetchone()[0]
            
            if exists == 0:
                print(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE candidate_reference_check ADD COLUMN {column_name} {column_type}")
                print(f"✓ Added {column_name}")
            else:
                print(f"✓ Column {column_name} already exists")
        
        # Commit changes
        connection.commit()
        print("\n🎉 All columns added successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure to:")
        print("1. Update the db_password variable with your actual MySQL password")
        print("2. Have MySQL running and accessible")
        print("3. Have the hrms_db database created")
        
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    add_missing_columns()
