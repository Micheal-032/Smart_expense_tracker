"""
Smart Personal Expense Tracker - Application Launcher
Run this file to start the application
"""

from database import init_database, create_sample_data
from app import app
import os

def initialize_app():
    """Initialize the application on first run"""
    # Check if database exists
    db_exists = os.path.exists('expense_tracker.db')
    
    # Initialize database schema
    print("Initializing database...")
    init_database()
    
    # Create sample data if database is new
    if not db_exists:
        print("Creating sample data...")
        create_sample_data()
    
    print("\n" + "="*60)
    print("Smart Personal Expense Tracker is ready!")
    print("="*60)
    print("\nAccess the application at: http://localhost:5000")
    print("\nDemo Login Credentials:")
    print("   Email: demo@expense.com")
    print("   Password: Password123")
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    # Initialize app
    initialize_app()
    
    # Run Flask development server
    app.run(debug=True, host='0.0.0.0', port=5000)
