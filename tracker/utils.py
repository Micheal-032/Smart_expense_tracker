"""
Advanced utility functions for new features
Includes audit logging, analytics calculations, and helper functions
"""

from database import get_db_connection
from datetime import datetime, timedelta
import json

# ========== AUDIT LOGGING ==========

def log_audit(user_id, action, entity, entity_id=None, details=None):
    """Log user action to audit trail"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    details_json = json.dumps(details) if details else None
    
    cursor.execute('''
        INSERT INTO audit_logs (user_id, action, entity, entity_id, details)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, action, entity, entity_id, details_json))
    
    conn.commit()
    conn.close()

# ========== ACCOUNT MANAGEMENT ==========

def create_default_account(user_id):
    """Create default cash account for new user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO accounts (user_id, account_name, balance, currency)
        VALUES (?, ?, ?, ?)
    ''', (user_id, 'Cash', 0, 'INR'))
    
    conn.commit()
    conn.close()

def update_account_balance(account_id, amount, operation='subtract'):
    """Update account balance"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if operation == 'subtract':
        cursor.execute('UPDATE accounts SET balance = balance - ? WHERE account_id = ?', (amount, account_id))
    else:
        cursor.execute('UPDATE accounts SET balance = balance + ? WHERE account_id = ?', (amount, account_id))
    
    conn.commit()
    conn.close()

# ========== ANALYTICS CALCULATIONS ==========

def calculate_health_score(user_id, month=None):
    """
    Calculate financial health score (0-100)
    Score = 100 - (Overspend% * 0.5) - (Impulse% * 0.3)
    """
    if not month:
        month = datetime.now().strftime('%Y-%m')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get monthly total
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ? AND is_deleted = 0 AND is_draft = 0
    ''', (user_id, month))
    monthly_total = cursor.fetchone()['total']
    
    # Get budget
    now = datetime.now()
    cursor.execute('''
        SELECT monthly_limit FROM budget
        WHERE user_id = ? AND month = ? AND year = ?
    ''', (user_id, now.month, now.year))
    budget_row = cursor.fetchone()
    monthly_budget = budget_row['monthly_limit'] if budget_row else 0
    
    conn.close()
    
    # Calculate overspend percentage
    overspend_pct = max(0, (monthly_total - monthly_budget) / monthly_budget * 100) if monthly_budget > 0 else 0
    
    # Simplified impulse calculation (can be enhanced)
    impulse_pct = 10  # Placeholder
    
    score = max(0, 100 - (overspend_pct * 0.5) - (impulse_pct * 0.3))
    
    return round(score, 2)

def calculate_spending_velocity(user_id):
    """
    Calculate spending velocity: avg daily spending this month
    Returns: current velocity, last month avg, comparison
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    current_month = now.strftime('%Y-%m')
    days_passed = now.day
    
    # Current month total
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ? AND is_deleted = 0 AND is_draft = 0
    ''', (user_id, current_month))
    current_total = cursor.fetchone()['total']
    
    # Last month total
    last_month_date = now - timedelta(days=30)
    last_month = last_month_date.strftime('%Y-%m')
    
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ? AND is_deleted = 0 AND is_draft = 0
    ''', (user_id, last_month))
    last_month_total = cursor.fetchone()['total']
    
    conn.close()
    
    current_velocity = current_total / days_passed if days_passed > 0 else 0
    last_month_velocity = last_month_total / 30
    
    comparison = 'higher' if current_velocity > last_month_velocity else 'lower'
    
    return {
        'current_velocity': round(current_velocity, 2),
        'last_month_velocity': round(last_month_velocity, 2),
        'comparison': comparison,
        'projected_monthly': round(current_velocity * 30, 2)
    }

def detect_cost_leaks(user_id, threshold=1000):
    """
    Detect small recurring costs that add up
    Returns categories where daily small expenses > threshold monthly
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_month = datetime.now().strftime('%Y-%m')
    
    cursor.execute('''
        SELECT c.category_name, AVG(e.amount) as avg_amount, COUNT(*) as frequency
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ? 
          AND strftime('%Y-%m', e.expense_date) = ?
          AND e.amount < 200
          AND e.is_deleted = 0
          AND e.is_draft = 0
        GROUP BY c.category_name
        HAVING (avg_amount * 30) > ?
    ''', (user_id, current_month, threshold))
    
    leaks = []
    for row in cursor.fetchall():
        leaks.append ({
            'category': row['category_name'],
            'avg_daily': round(row['avg_amount'], 2),
            'monthly_impact': round(row['avg_amount'] * 30, 2),
            'frequency': row['frequency']
        })
    
    conn.close()
    return leaks

def determine_financial_personality(user_id):
    """
    Determine user's financial personality
    Saver: < 70% budget, Balanced: 70-90%, Spender: > 90%
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    current_month = now.strftime('%Y-%m')
    
    # Get monthly spending
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ? AND is_deleted = 0 AND is_draft = 0
    ''', (user_id, current_month))
    monthly_total = cursor.fetchone()['total']
    
    # Get budget
    cursor.execute('''
        SELECT monthly_limit FROM budget
        WHERE user_id = ? AND month = ? AND year = ?
    ''', (user_id, now.month, now.year))
    budget_row = cursor.fetchone()
    monthly_budget = budget_row['monthly_limit'] if budget_row else 0
    
    conn.close()
    
    if monthly_budget == 0:
        return {'personality': 'Unknown', 'percentage': 0}
    
    percentage = (monthly_total / monthly_budget) * 100
    
    if percentage < 70:
        personality = 'Saver'
    elif percentage <= 90:
        personality = 'Balanced'
    else:
        personality = 'Spender'
    
    return {
        'personality': personality,
        'percentage': round(percentage, 2),
        'spent': monthly_total,
        'budget': monthly_budget
    }

def check_duplicate_expense(user_id, amount, category_id, expense_date):
    """Check if similar expense exists on same date"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT expense_id, amount, note
        FROM expenses
        WHERE user_id = ? 
          AND category_id = ? 
          AND expense_date = ?
          AND ABS(amount - ?) < 0.01
          AND is_deleted = 0
        LIMIT 1
    ''', (user_id, category_id, expense_date, amount))
    
    duplicate = cursor.fetchone()
    conn.close()
    
    if duplicate:
        return {
            'is_duplicate': True,
            'expense_id': duplicate['expense_id'],
            'amount': duplicate['amount'],
            'note': duplicate['note']
        }
    
    return {'is_duplicate': False}

# ========== RECURRING EXPENSE PROCESSING ==========

def process_recurring_expenses():
    """Process all active recurring expenses and create due expenses"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now().date()
    processed_count = 0
    
    # Get all active recurring expenses
    cursor.execute('''
        SELECT * FROM recurring_expenses
        WHERE is_active = 1
    ''')
    
    for recurring in cursor.fetchall():
        should_create = False
        
        # Check if expense is due based on cycle
        if recurring['last_added']:
            last_added = datetime.strptime(recurring['last_added'], '%Y-%m-%d').date()
            
            if recurring['cycle'] == 'daily':
                should_create = (today - last_added).days >= 1
            elif recurring['cycle'] == 'weekly':
                should_create = (today - last_added).days >= 7
            elif recurring['cycle'] == 'monthly':
                should_create = (today - last_added).days >= 30
        else:
            should_create = True  # First time
        
        if should_create:
            # Create the expense
            cursor.execute('''
                INSERT INTO expenses (user_id, category_id, amount, payment_mode, note, expense_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                recurring['user_id'],
                recurring['category_id'],
                recurring['amount'],
                recurring['payment_mode'],
                f"[Auto] {recurring['note']}" if recurring['note'] else '[Auto] Recurring expense',
                today.strftime('%Y-%m-%d')
            ))
            
            # Update last_added
            cursor.execute('''
                UPDATE recurring_expenses
                SET last_added = ?
                WHERE recurring_id = ?
            ''', (today.strftime('%Y-%m-%d'), recurring['recurring_id']))
            
            processed_count += 1
    
    conn.commit()
    conn.close()
    
    return processed_count
