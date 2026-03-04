"""
Database Migration: Add Password Reset Table

This migration adds the password_resets table for secure password reset functionality.
"""

import sqlite3
from datetime import datetime

def run_password_reset_migration(db_path='expense_tracker.db'):
    """Add password_resets table to the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Creating password_resets table...")
        
        # Create password_resets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_resets (
                reset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL UNIQUE,
                otp TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                is_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_password_reset_token ON password_resets(token)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_password_reset_user_id ON password_resets(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_password_reset_expires_at ON password_resets(expires_at)')
        
        conn.commit()
        print("[OK] password_resets table created successfully")
        print("[OK] Indexes created")
        
        # Verify table structure
        cursor.execute("PRAGMA table_info(password_resets)")
        columns = cursor.fetchall()
        print(f"[OK] Table has {len(columns)} columns")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error during migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    success = run_password_reset_migration()
    if success:
        print("\n=== Password reset migration completed successfully ===")
    else:
        print("\n=== Password reset migration failed ===")
