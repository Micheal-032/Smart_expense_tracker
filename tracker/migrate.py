"""
Database Migration Script for Advanced Features
Extends existing schema with new tables and columns
"""

import sqlite3
from database import DATABASE_NAME

def run_migration():
    """Run database migration to add new tables and columns"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    # Check if migration already ran
    cursor.execute("PRAGMA table_info(categories)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'is_favorite' in columns:
        print("Migration already completed!")
        conn.close()
        return
    
    try:
        # ========== ALTER EXISTING TABLES ==========
        
        # Add columns to categories table
        print("Adding is_favorite to categories table...")
        cursor.execute("ALTER TABLE categories ADD COLUMN is_favorite INTEGER DEFAULT 0")
        
        # Add columns to expenses table
        print("Adding new columns to expenses table...")
        cursor.execute("ALTER TABLE expenses ADD COLUMN tags TEXT")
        cursor.execute("ALTER TABLE expenses ADD COLUMN is_deleted INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE expenses ADD COLUMN account_id INTEGER")
        cursor.execute("ALTER TABLE expenses ADD COLUMN is_draft INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE expenses ADD COLUMN deleted_at TIMESTAMP")
        
        # ========== CREATE NEW TABLES ==========
        
        # Accounts (Wallets) table
        print("Creating accounts table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_name TEXT NOT NULL,
                balance REAL DEFAULT 0,
                currency TEXT DEFAULT 'INR',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Recurring Expenses table
        print("Creating recurring_expenses table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recurring_expenses (
                recurring_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                payment_mode TEXT NOT NULL,
                note TEXT,
                cycle TEXT NOT NULL,
                last_added DATE,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        ''')
        
        # Audit Logs table
        print("Creating audit_logs table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                entity TEXT NOT NULL,
                entity_id INTEGER,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Savings Goals table
        print("Creating savings_goals table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS savings_goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                deadline DATE,
                is_achieved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Spending Challenges table
        print("Creating spending_challenges table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spending_challenges (
                challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                challenge_name TEXT NOT NULL,
                daily_limit REAL NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_active INTEGER DEFAULT 1,
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Currency Rates table
        print("Creating currency_rates table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS currency_rates (
                rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_currency TEXT NOT NULL,
                to_currency TEXT NOT NULL,
                rate REAL NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_currency, to_currency)
            )
        ''')
        
        # ========== SEED DEFAULT DATA ==========
        
        # Add default currency rates
        print("Seeding default currency rates...")
        default_rates = [
            ('USD', 'INR', 83.0),
            ('EUR', 'INR', 90.0),
            ('GBP', 'INR', 105.0),
            ('INR', 'INR', 1.0)
        ]
        
        for from_curr, to_curr, rate in default_rates:
            cursor.execute(
                'INSERT OR IGNORE INTO currency_rates (from_currency, to_currency, rate) VALUES (?, ?, ?)',
                (from_curr, to_curr, rate)
            )
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()
