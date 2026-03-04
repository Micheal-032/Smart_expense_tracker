"""
Database initialization and management for Smart Personal Expense Tracker
Contains all database schema definitions and utility functions
"""

import sqlite3
from datetime import datetime, timedelta
import random

DATABASE_NAME = 'expense_tracker.db'

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def init_database():
    """Initialize database with all required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, category_name)
        )
    ''')
    
    # Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_mode TEXT NOT NULL,
            note TEXT,
            expense_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id)
        )
    ''')
    
    # Budget table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budget (
            budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            monthly_limit REAL NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, month, year)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def create_default_categories(user_id):
    """Create default categories for a new user"""
    default_categories = ['Food', 'Transport', 'Rent', 'Shopping', 'Medical', 'Entertainment']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for category in default_categories:
        try:
            cursor.execute(
                'INSERT INTO categories (user_id, category_name) VALUES (?, ?)',
                (user_id, category)
            )
        except sqlite3.IntegrityError:
            pass  # Category already exists
    
    conn.commit()
    conn.close()

def create_sample_data():
    """Create sample data for demo purposes"""
    from auth_utils import hash_password
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if demo user already exists
    cursor.execute('SELECT user_id FROM users WHERE email = ?', ('demo@expense.com',))
    if cursor.fetchone():
        conn.close()
        print("Sample data already exists")
        return
    
    # Create demo user
    demo_password = hash_password('Password123')
    cursor.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        ('Demo User', 'demo@expense.com', demo_password)
    )
    demo_user_id = cursor.lastrowid
    
    # Create default categories for demo user (inline to avoid connection issues)
    default_categories = ['Food', 'Transport', 'Rent', 'Shopping', 'Medical', 'Entertainment']
    for category in default_categories:
        cursor.execute(
            'INSERT INTO categories (user_id, category_name) VALUES (?, ?)',
            (demo_user_id, category)
        )
    
    # Get category IDs
    cursor.execute('SELECT category_id, category_name FROM categories WHERE user_id = ?', (demo_user_id,))
    categories = {row['category_name']: row['category_id'] for row in cursor.fetchall()}
    
    # Sample expense data
    payment_modes = ['Cash', 'UPI', 'Card']
    sample_notes = [
        'Lunch at restaurant',
        'Metro ticket',
        'Monthly rent',
        'Grocery shopping',
        'Doctor visit',
        'Movie tickets',
        'Coffee',
        'Taxi fare',
        'Online shopping',
        'Medicines',
        'Dinner',
        'Bus pass',
        'Vegetables',
        'Concert tickets',
        ''
    ]
    
    # Generate 50 sample expenses over last 30 days
    today = datetime.now()
    for i in range(50):
        days_ago = random.randint(0, 30)
        expense_date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        category_name = random.choice(list(categories.keys()))
        category_id = categories[category_name]
        
        # Amount varies by category
        amount_ranges = {
            'Food': (50, 500),
            'Transport': (20, 300),
            'Rent': (5000, 15000),
            'Shopping': (200, 2000),
            'Medical': (100, 1500),
            'Entertainment': (150, 1000)
        }
        min_amt, max_amt = amount_ranges.get(category_name, (100, 1000))
        amount = round(random.uniform(min_amt, max_amt), 2)
        
        payment_mode = random.choice(payment_modes)
        note = random.choice(sample_notes)
        
        cursor.execute(
            '''INSERT INTO expenses (user_id, category_id, amount, payment_mode, note, expense_date)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (demo_user_id, category_id, amount, payment_mode, note, expense_date)
        )
    
    # Set monthly budget for demo user
    current_month = today.month
    current_year = today.year
    cursor.execute(
        'INSERT INTO budget (user_id, monthly_limit, month, year) VALUES (?, ?, ?, ?)',
        (demo_user_id, 30000, current_month, current_year)
    )
    
    conn.commit()
    conn.close()
    print("Sample data created successfully")
    print("Demo Login: demo@expense.com / Password123")

if __name__ == '__main__':
    init_database()
    create_sample_data()
