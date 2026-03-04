"""
Comprehensive PDF Documentation Generator for Expense Tracker
Generates A-Z documentation with SQL schema highlights and code examples
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, Preformatted
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os

# Colors
PRIMARY = colors.HexColor('#667eea')
SECONDARY = colors.HexColor('#764ba2')
CODE_BG = colors.HexColor('#f5f5f5')
SQL_HIGHLIGHT = colors.HexColor('#e8f5e9')

class DocCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.grey)
        self.drawRightString(letter[0] - 0.75*inch, 0.5*inch, f"Page {self._pageNumber} of {page_count}")
        self.drawString(0.75*inch, 0.5*inch, "Expense Tracker - Complete Documentation")

def create_documentation():
    filename = f"Expense_Tracker_Complete_Documentation_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=0.75*inch, leftMargin=0.75*inch,
                           topMargin=1*inch, bottomMargin=1*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=32,
                                 textColor=PRIMARY, spaceAfter=30, alignment=TA_CENTER,
                                 fontName='Helvetica-Bold')
    
    h1_style = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=20,
                             textColor=SECONDARY, spaceAfter=16, spaceBefore=20,
                             fontName='Helvetica-Bold')
    
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=16,
                             textColor=PRIMARY, spaceAfter=12, spaceBefore=12,
                             fontName='Helvetica-Bold')
    
    h3_style = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=14,
                             spaceAfter=10, spaceBefore=10, fontName='Helvetica-Bold')
    
    code_style = ParagraphStyle('Code', parent=styles['Code'], fontSize=9,
                               leftIndent=20, rightIndent=20, spaceAfter=12,
                               fontName='Courier', backColor=CODE_BG)
    
    normal = styles['Normal']
    normal.fontSize = 11
    normal.leading = 14
    
    # COVER PAGE
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("💰 EXPENSE TRACKER", title_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Complete A-Z Technical Documentation</b>", 
                             ParagraphStyle('Subtitle', parent=normal, fontSize=18, alignment=TA_CENTER)))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("Full-Stack Multi-User Expense Management System", 
                             ParagraphStyle('Subtitle2', parent=normal, fontSize=14, alignment=TA_CENTER)))
    elements.append(Spacer(1, 1*inch))
    
    cover_info = [
        ['Technology Stack', 'Python Flask + SQLite + HTML/CSS/JS'],
        ['Database', 'SQLite with Multi-User Isolation'],
        ['Architecture', 'MVC Pattern with RESTful APIs'],
        ['Security', 'PBKDF2-SHA256 Password Hashing'],
        ['Generated', datetime.now().strftime('%B %d, %Y at %I:%M %p')]
    ]
    
    cover_table = Table(cover_info, colWidths=[2.5*inch, 4*inch])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.white)
    ]))
    
    elements.append(cover_table)
    elements.append(PageBreak())
    
    # TABLE OF CONTENTS
    elements.append(Paragraph("Table of Contents", h1_style))
    elements.append(Spacer(1, 0.2*inch))
    
    toc_items = [
        "1. Executive Summary",
        "2. System Architecture Overview",
        "3. Database Schema (Complete SQL)",
        "4. Core Modules & Code Structure",
        "5. Authentication System",
        "6. Expense Management",
        "7. Advanced Features",
        "8. API Endpoints Reference",
        "9. Frontend Components",
        "10. Security Implementation",
        "11. Installation & Deployment",
        "12. Usage Guide"
    ]
    
    for item in toc_items:
        elements.append(Paragraph(f"• {item}", normal))
        elements.append(Spacer(1, 0.1*inch))
    
    elements.append(PageBreak())
    
    # 1. EXECUTIVE SUMMARY
    elements.append(Paragraph("1. Executive Summary", h1_style))
    elements.append(Paragraph("""
    The Smart Personal Expense Tracker is a professional-grade, multi-user web application built with Python Flask 
    and SQLite. It provides complete expense tracking capabilities with user isolation, advanced analytics, 
    budget management, and smart insights. The system features a modern, responsive UI with glassmorphism design, 
    secure authentication, and comprehensive reporting capabilities.
    """, normal))
    elements.append(Spacer(1, 0.2*inch))
    
    features_data = [
        ['Feature Category', 'Capabilities'],
        ['Authentication', 'Secure signup/login, password reset, session management'],
        ['Expense Management', 'CRUD operations, categories, payment modes, soft delete'],
        ['Analytics', 'Dashboard, reports, trends, health score, spending velocity'],
        ['Advanced Features', 'Recurring expenses, goals, challenges, accounts, audit logs'],
        ['Security', 'Password hashing, SQL injection prevention, data isolation'],
        ['UI/UX', 'Responsive design, dark theme, animations, premium typography']
    ]
    
    features_table = Table(features_data, colWidths=[2*inch, 4.5*inch])
    features_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, CODE_BG])
    ]))
    
    elements.append(features_table)
    elements.append(PageBreak())
    
    # 2. SYSTEM ARCHITECTURE
    elements.append(Paragraph("2. System Architecture Overview", h1_style))
    elements.append(Paragraph("2.1 Technology Stack", h2_style))
    
    tech_stack = """
    <b>Backend:</b> Python 3.7+ with Flask 3.0 framework<br/>
    <b>Database:</b> SQLite with row-level user isolation<br/>
    <b>Frontend:</b> HTML5, CSS3, Vanilla JavaScript<br/>
    <b>Security:</b> Werkzeug PBKDF2-SHA256 password hashing<br/>
    <b>PDF Generation:</b> ReportLab library<br/>
    <b>Email:</b> SMTP integration for reports and password reset
    """
    elements.append(Paragraph(tech_stack, normal))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("2.2 Project Structure", h2_style))
    
    structure_code = """
tracker/
├── app.py                      # Main Flask application (1101 lines)
├── database.py                 # Database schema & initialization (196 lines)
├── auth_utils.py              # Authentication utilities (63 lines)
├── utils.py                   # Advanced utility functions (313 lines)
├── api_advanced.py            # Extended API endpoints (677 lines)
├── pdf_report_generator.py    # PDF report generation (406 lines)
├── email_service.py           # Email functionality
├── password_reset_api.py      # Password reset logic
├── migrate.py                 # Database migrations (166 lines)
├── run.py                     # Application launcher
├── requirements.txt           # Python dependencies
├── expense_tracker.db         # SQLite database (auto-generated)
├── static/
│   ├── css/
│   │   └── style.css         # Complete design system
│   └── js/
└── templates/                 # 14 HTML templates
    ├── login.html
    ├── signup.html
    ├── dashboard.html
    ├── expenses.html
    ├── reports.html
    ├── categories.html
    ├── profile.html
    ├── accounts.html
    ├── recurring.html
    ├── goals.html
    ├── challenges.html
    ├── analytics.html
    ├── forgot_password.html
    └── reset_password.html
"""
    
    elements.append(Preformatted(structure_code, code_style))
    elements.append(PageBreak())
    
    # 3. DATABASE SCHEMA - COMPLETE SQL
    elements.append(Paragraph("3. Database Schema - Complete SQL", h1_style))
    elements.append(Paragraph("""
    This section contains the complete SQL schema for all database tables. The system uses SQLite 
    with foreign key constraints and proper indexing for optimal performance.
    """, normal))
    elements.append(Spacer(1, 0.2*inch))
    
    # Users Table
    elements.append(Paragraph("3.1 Users Table", h2_style))
    users_sql = """CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stores all user accounts with secure password hashing
-- Email is unique constraint for login identification
-- password_hash uses PBKDF2-SHA256 algorithm"""
    
    elements.append(Preformatted(users_sql, ParagraphStyle('SQLCode', parent=code_style, backColor=SQL_HIGHLIGHT)))
    elements.append(Spacer(1, 0.2*inch))
    
    # Categories Table
    elements.append(Paragraph("3.2 Categories Table", h2_style))
    categories_sql = """CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_name TEXT NOT NULL,
    is_favorite INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, category_name)
);

-- User-specific expense categories
-- Default categories: Food, Transport, Rent, Shopping, Medical, Entertainment
-- Users can add custom categories
-- is_favorite flag for quick access to frequently used categories"""
    
    elements.append(Preformatted(categories_sql, ParagraphStyle('SQLCode', parent=code_style, backColor=SQL_HIGHLIGHT)))
    elements.append(Spacer(1, 0.2*inch))
    
    # Expenses Table
    elements.append(Paragraph("3.3 Expenses Table (Core)", h2_style))
    expenses_sql = """CREATE TABLE expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_mode TEXT NOT NULL,  -- Cash, UPI, Card
    note TEXT,
    expense_date DATE NOT NULL,
    tags TEXT,                   -- Comma-separated tags
    is_deleted INTEGER DEFAULT 0,  -- Soft delete flag
    is_draft INTEGER DEFAULT 0,    -- Draft expenses
    account_id INTEGER,            -- Linked account/wallet
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Main expense tracking table
-- Supports soft delete (recycle bin feature)
-- Draft mode for incomplete entries
-- Tags for flexible categorization"""
    
    elements.append(Preformatted(expenses_sql, ParagraphStyle('SQLCode', parent=code_style, backColor=SQL_HIGHLIGHT)))
    elements.append(PageBreak())
    
    # Budget Table
    elements.append(Paragraph("3.4 Budget Table", h2_style))
    budget_sql = """CREATE TABLE budget (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    monthly_limit REAL NOT NULL,
    month INTEGER NOT NULL,      -- 1-12
    year INTEGER NOT NULL,       -- YYYY
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, month, year)
);

-- Monthly budget limits per user
-- Unique constraint ensures one budget per month per user
-- Used for budget warnings and financial health score"""
    
    elements.append(Preformatted(budget_sql, ParagraphStyle('SQLCode', parent=code_style, backColor=SQL_HIGHLIGHT)))
    elements.append(Spacer(1, 0.2*inch))
    
    # Accounts Table
    elements.append(Paragraph("3.5 Accounts/Wallets Table", h2_style))
    accounts_sql = """CREATE TABLE accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    account_name TEXT NOT NULL,
    balance REAL DEFAULT 0,
    currency TEXT DEFAULT 'INR',
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Multiple account/wallet support
-- Track balances across different payment sources
-- Multi-currency support (INR, USD, EUR, GBP)
-- Soft delete via is_active flag"""
    
    elements.append(Preformatted(accounts_sql, ParagraphStyle('SQLCode', parent=code_style, backColor=SQL_HIGHLIGHT)))
    elements.append(Spacer(1, 0.2*inch))
    
    # Recurring Expenses Table
    elements.append(Paragraph("3.6 Recurring Expenses Table", h2_style))
    recurring_sql = """CREATE TABLE recurring_expenses (
    recurring_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_mode TEXT NOT NULL,
    note TEXT,
    cycle TEXT NOT NULL,         -- 'daily', 'weekly', 'monthly'
    last_added DATE,             -- Last auto-generated date
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

-- Automated recurring expense management
-- Supports daily, weekly, and monthly cycles
-- Auto-generates expenses based on cycle
-- last_added tracks when expense was last created"""
    
    elements.append(Preformatted(recurring_sql, ParagraphStyle('SQLCode', parent=code_style, backColor=SQL_HIGHLIGHT)))
    elements.append(PageBreak())
    
    # Savings Goals Table
    elements.append(Paragraph("3.7 Savings Goals Table", h2_style))
    goals_sql = """CREATE TABLE savings_goals (
    goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    goal_name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL DEFAULT 0,
    deadline DATE,
    is_achieved INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Financial goal tracking
-- Progress monitoring with current vs target amounts
-- Deadline-based goal management
-- Achievement flag for completed goals"""
    
    elements.append(Preformatted(goals_sql, ParagraphStyle('SQLCode', parent=code_style, backColor=SQL_HIGHLIGHT)))
    elements.append(Spacer(1, 0.2*inch))
    
    # Spending Challenges Table
    elements.append(Paragraph("3.8 Spending Challenges Table", h2_style))
    challenges_sql = """CREATE TABLE spending_challenges (
    challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    challenge_name TEXT NOT NULL,
    daily_limit REAL NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 0,  -- Days under limit
    fail_count INTEGER DEFAULT 0,     -- Days over limit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Gamification feature for spending control
-- Daily spending limit challenges
-- Success/fail tracking for motivation
-- Date range for challenge duration"""
    
    elements.append(Preformatted(challenges_sql, ParagraphStyle('SQLCode', parent=code_style, backColor=SQL_HIGHLIGHT)))
    elements.append(Spacer(1, 0.2*inch))
    
    # Audit Logs Table
    elements.append(Paragraph("3.9 Audit Logs Table", h2_style))
    audit_sql = """CREATE TABLE audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,        -- CREATE, UPDATE, DELETE, etc.
    entity TEXT NOT NULL,        -- expense, category, account, etc.
    entity_id INTEGER,
    details TEXT,                -- JSON string with additional info
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Complete audit trail for all user actions
-- Tracks who did what and when
-- Details field stores JSON for complex data
-- Essential for debugging and compliance"""
    
    elements.append(Preformatted(audit_sql, ParagraphStyle('SQLCode', parent=code_style, backColor=SQL_HIGHLIGHT)))
    elements.append(PageBreak())
    
    # Password Reset Table
    elements.append(Paragraph("3.10 Password Reset Table", h2_style))
    reset_sql = """CREATE TABLE password_resets (
    reset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    otp TEXT NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Secure password reset mechanism
-- Token + OTP dual verification
-- Expiration timestamp for security
-- is_used prevents token reuse"""
    
    elements.append(Preformatted(reset_sql, ParagraphStyle('SQLCode', parent=code_style, backColor=SQL_HIGHLIGHT)))
    elements.append(Spacer(1, 0.2*inch))
    
    # Currency Rates Table
    elements.append(Paragraph("3.11 Currency Rates Table", h2_style))
    currency_sql = """CREATE TABLE currency_rates (
    rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_currency TEXT NOT NULL,
    to_currency TEXT NOT NULL,
    rate REAL NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_currency, to_currency)
);

-- Multi-currency support
-- Exchange rate storage
-- Default rates: USD, EUR, GBP to INR
-- Can be updated for real-time rates"""
    
    elements.append(Preformatted(currency_sql, ParagraphStyle('SQLCode', parent=code_style, backColor=SQL_HIGHLIGHT)))
    elements.append(PageBreak())
    
    # 4. CORE MODULES
    elements.append(Paragraph("4. Core Modules & Code Structure", h1_style))
    
    elements.append(Paragraph("4.1 app.py - Main Application (1101 lines)", h2_style))
    elements.append(Paragraph("""
    The main Flask application file containing all route handlers and business logic. 
    Organized into logical sections: Authentication, Dashboard, Expenses, Categories, Reports, Budget, and Profile.
    """, normal))
    
    app_structure = """
<b>Key Sections:</b>
• Authentication Routes (/login, /signup, /logout, /forgot-password, /reset-password)
• Dashboard Routes (/dashboard, /api/dashboard/summary, /api/dashboard/trends)
• Expense CRUD (/api/expenses - GET, POST, PUT, DELETE)
• Category Management (/api/categories)
• Reports & Analytics (/api/reports/monthly, /api/reports/daily)
• Budget Management (/api/budget)
• Profile & Settings (/profile, /api/profile/update)
• PDF Report Generation (/api/reports/download-pdf)
• Email Report Service (/api/reports/email-monthly)

<b>Code Highlights:</b>
"""
    elements.append(Paragraph(app_structure, normal))
    
    app_code = """# Example: Add Expense Endpoint with Validation
@app.route('/api/expenses', methods=['POST'])
@login_required
def api_add_expense():
    user_id = get_current_user_id()
    data = request.get_json()
    
    amount = data.get('amount')
    category_id = data.get('category_id')
    payment_mode = data.get('payment_mode')
    expense_date = data.get('date')
    note = data.get('note', '').strip()
    
    # Validation
    if not all([amount, category_id, payment_mode, expense_date]):
        return jsonify({'success': False, 
                       'message': 'All required fields must be provided'}), 400
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify category belongs to user (security check)
    cursor.execute('SELECT category_id FROM categories WHERE category_id = ? AND user_id = ?', 
                   (category_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid category'}), 400
    
    # Insert expense
    cursor.execute('''
        INSERT INTO expenses (user_id, category_id, amount, payment_mode, note, expense_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, category_id, amount, payment_mode, note, expense_date))
    
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Expense added successfully',
        'expense_id': expense_id
    }), 201"""
    
    elements.append(Preformatted(app_code, code_style))
    elements.append(PageBreak())
    
    elements.append(Paragraph("4.2 database.py - Schema & Initialization", h2_style))
    
    db_code = """def init_database():
    \"\"\"Initialize database with all required tables\"\"\"
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
    
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def create_default_categories(user_id):
    \"\"\"Create default categories for a new user\"\"\"
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
    conn.close()"""
    
    elements.append(Preformatted(db_code, code_style))
    elements.append(PageBreak())
    
    elements.append(Paragraph("4.3 auth_utils.py - Authentication Utilities", h2_style))
    
    auth_code = """from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, url_for, jsonify
import re

def hash_password(password):
    \"\"\"Hash a password using werkzeug's secure method\"\"\"
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(password_hash, password):
    \"\"\"Verify a password against its hash\"\"\"
    return check_password_hash(password_hash, password)

def validate_email(email):
    \"\"\"Validate email format\"\"\"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    \"\"\"
    Validate password strength
    Requirements: At least 8 characters, contains letter and number
    \"\"\"
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def login_required(f):
    \"\"\"Decorator to require login for a route\"\"\"
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if '/api/' in str(f):
                return jsonify({'success': False, 'message': 'Login required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function"""
    
    elements.append(Preformatted(auth_code, code_style))
    elements.append(PageBreak())
    
    # Build PDF
    doc.build(elements, canvasmaker=DocCanvas)
    print(f"\n[SUCCESS] Documentation generated: {filename}")
    print(f"[INFO] File size: {os.path.getsize(filename) / 1024:.2f} KB")
    return filename

if __name__ == '__main__':
    create_documentation()
