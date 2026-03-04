"""
Smart Personal Expense Tracker - Main Application
A professional multi-user expense tracking web application
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from database import get_db_connection, init_database, create_default_categories
from auth_utils import (
    hash_password, verify_password, validate_email, validate_password,
    login_required, get_current_user_id, set_current_user, clear_session
)
from utils import log_audit
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # Secure secret key for sessions
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Clean up expired password resets on startup
try:
    from password_reset_api import cleanup_expired_resets
    cleanup_expired_resets()
except Exception as e:
    print(f"Note: Password reset cleanup skipped: {e}")

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login')
def login():
    """Render login page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/signup')
def signup():
    """Render signup page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    """User registration endpoint"""
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    # Validation
    if not name or not email or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    if not validate_email(email):
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    is_valid, msg = validate_password(password)
    if not is_valid:
        return jsonify({'success': False, 'message': msg}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if email already exists
    cursor.execute('SELECT user_id FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    # Create user
    password_hash = hash_password(password)
    cursor.execute(
        'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
        (name, email, password_hash)
    )
    user_id = cursor.lastrowid
    conn.commit()
    
    # Create default categories for new user
    create_default_categories(user_id)
    
    # Create default account (Cash)
    from utils import create_default_account
    create_default_account(user_id)
    
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Account created successfully! Please login.'
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """User login endpoint"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id, name, email, password_hash FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not verify_password(user['password_hash'], password):
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401
    
    # Set session
    set_current_user(user['user_id'], user['email'], user['name'])
    session.permanent = True
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user': {'name': user['name'], 'email': user['email']}
    }), 200

@app.route('/logout')
def logout():
    """Logout user"""
    clear_session()
    return redirect(url_for('login'))

# ==================== PASSWORD RESET ROUTES ====================

@app.route('/forgot-password')
def forgot_password_page():
    """Render forgot password page"""
    return render_template('forgot_password.html')

@app.route('/reset-password')
def reset_password_page():
    """Render reset password page"""
    token = request.args.get('token', '')
    return render_template('reset_password.html', token=token)

@app.route('/api/auth/forgot-password', methods=['POST'])
def api_forgot_password():
    """Request password reset"""
    from password_reset_api import create_password_reset_request
    
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    
    result = create_password_reset_request(email)
    return jsonify(result), 200

@app.route('/api/auth/reset-password', methods=['POST'])
def api_reset_password():
    """Reset password with token and OTP"""
    from password_reset_api import validate_reset_token, update_user_password
    
    data = request.get_json()
    token = data.get('token', '')
    otp = data.get('otp', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    # Validation
    if not token or not otp or not new_password or not confirm_password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
    
    # Validate password strength
    is_valid, msg = validate_password(new_password)
    if not is_valid:
        return jsonify({'success': False, 'message': msg}), 400
    
    # Validate token and OTP
    validation_result = validate_reset_token(token, otp)
    if not validation_result['success']:
        return jsonify(validation_result), 400
    
    # Update password
    update_result = update_user_password(
        validation_result['user_id'],
        validation_result['reset_id'],
        new_password
    )
    
    return jsonify(update_result), 200 if update_result['success'] else 400

# ==================== DASHBOARD ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Render main dashboard"""
    return render_template('dashboard.html')

@app.route('/api/dashboard/summary', methods=['GET'])
@login_required
def api_dashboard_summary():
    """Get dashboard summary statistics"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Current month and year
    now = datetime.now()
    current_month = now.strftime('%Y-%m')
    today = now.strftime('%Y-%m-%d')
    
    # Total monthly spending (excluding deleted and drafts)
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
          AND is_deleted = 0 AND is_draft = 0
    ''', (user_id, current_month))
    monthly_total = cursor.fetchone()['total']
    
    # Today's spending
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE user_id = ? AND expense_date = ?
          AND is_deleted = 0 AND is_draft = 0
    ''', (user_id, today))
    today_total = cursor.fetchone()['total']
    
    # Top spending category this month
    cursor.execute('''
        SELECT c.category_name, SUM(e.amount) as total
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
        GROUP BY c.category_name
        ORDER BY total DESC
        LIMIT 1
    ''', (user_id, current_month))
    top_category_row = cursor.fetchone()
    top_category = top_category_row['category_name'] if top_category_row else 'None'
    top_category_amount = top_category_row['total'] if top_category_row else 0
    
    # Check if no expenses added today for reminder
    cursor.execute('''
        SELECT COUNT(*) as count
        FROM expenses
        WHERE user_id = ? AND expense_date = ?
    ''', (user_id, today))
    no_expense_today = cursor.fetchone()['count'] == 0
    
    # Budget status
    cursor.execute('''
        SELECT monthly_limit
        FROM budget
        WHERE user_id = ? AND month = ? AND year = ?
    ''', (user_id, now.month, now.year))
    budget_row = cursor.fetchone()
    monthly_budget = budget_row['monthly_limit'] if budget_row else 0
    budget_percentage = (monthly_total / monthly_budget * 100) if monthly_budget > 0 else 0
    
    # Category-wise breakdown for insights
    cursor.execute('''
        SELECT c.category_name, SUM(e.amount) as total
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
        GROUP BY c.category_name
    ''', (user_id, current_month))
    category_breakdown = [{'category': row['category_name'], 'amount': row['total']} 
                          for row in cursor.fetchall()]
    
    # Calculate food percentage for smart insight
    food_total = next((item['amount'] for item in category_breakdown if item['category'] == 'Food'), 0)
    food_percentage = (food_total / monthly_total * 100) if monthly_total > 0 else 0
    
    conn.close()
    
    # Smart insights
    insights = []
    if food_percentage > 40:
        insights.append({
            'type': 'warning',
            'message': f'You are spending more on food this month ({food_percentage:.1f}%)'
        })
    if budget_percentage >= 80:
        insights.append({
            'type': 'danger',
            'message': f'You\'ve reached {budget_percentage:.1f}% of your monthly budget!'
        })
    if no_expense_today:
        insights.append({
            'type': 'info',
            'message': 'Don\'t forget to log your expenses today!'
        })
    
    return jsonify({
        'success': True,
        'data': {
            'monthly_total': round(monthly_total, 2),
            'today_total': round(today_total, 2),
            'top_category': top_category,
            'top_category_amount': round(top_category_amount, 2),
            'budget': round(monthly_budget, 2),
            'budget_spent': round(monthly_total, 2),
            'budget_percentage': round(budget_percentage, 2),
            'category_breakdown': category_breakdown,
            'insights': insights
        }
    }), 200

@app.route('/api/dashboard/trends', methods=['GET'])
@login_required
def api_dashboard_trends():
    """Get daily expense trends for current month"""
    user_id = get_current_user_id()
    current_month = datetime.now().strftime('%Y-%m')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT expense_date, SUM(amount) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
        GROUP BY expense_date
        ORDER BY expense_date ASC
    ''', (user_id, current_month))
    
    trends = [{'date': row['expense_date'], 'amount': round(row['total'], 2)} 
              for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({'success': True, 'data': trends}), 200

# ==================== EXPENSE ROUTES ====================

@app.route('/expenses')
@login_required
def expenses():
    """Render expense management page"""
    return render_template('expenses.html')

@app.route('/api/expenses', methods=['GET'])
@login_required
def api_get_expenses():
    """Get all active expenses for current user (excluding deleted and drafts)"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.expense_id, e.amount, e.payment_mode, e.note, e.expense_date, e.tags,
               c.category_name, c.category_id
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ? AND e.is_deleted = 0 AND e.is_draft = 0
        ORDER BY e.expense_date DESC, e.created_at DESC
    ''', (user_id,))
    
    expenses = [{
        'expense_id': row['expense_id'],
        'amount': round(row['amount'], 2),
        'category': row['category_name'],
        'category_id': row['category_id'],
        'payment_mode': row['payment_mode'],
        'note': row['note'] or '',
        'date': row['expense_date'],
        'tags': row['tags'] or ''
    } for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({'success': True, 'data': expenses}), 200

@app.route('/api/expenses', methods=['POST'])
@login_required
def api_add_expense():
    """Add a new expense"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    amount = data.get('amount')
    category_id = data.get('category_id')
    payment_mode = data.get('payment_mode')
    expense_date = data.get('date')
    note = data.get('note', '').strip()
    
    # Validation
    if not all([amount, category_id, payment_mode, expense_date]):
        return jsonify({'success': False, 'message': 'All required fields must be provided'}), 400
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid amount'}), 400
    
    if payment_mode not in ['Cash', 'UPI', 'Card']:
        return jsonify({'success': False, 'message': 'Invalid payment mode'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify category belongs to user
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
    }), 201

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
@login_required
def api_update_expense(expense_id):
    """Update an existing expense"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify expense belongs to user
    cursor.execute('SELECT expense_id FROM expenses WHERE expense_id = ? AND user_id = ?', 
                   (expense_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Expense not found'}), 404
    
    # Update fields
    amount = float(data.get('amount'))
    category_id = data.get('category_id')
    payment_mode = data.get('payment_mode')
    expense_date = data.get('date')
    note = data.get('note', '').strip()
    
    cursor.execute('''
        UPDATE expenses
        SET amount = ?, category_id = ?, payment_mode = ?, expense_date = ?, note = ?
        WHERE expense_id = ? AND user_id = ?
    ''', (amount, category_id, payment_mode, expense_date, note, expense_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Expense updated successfully'}), 200

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def api_delete_expense(expense_id):
    """Soft delete an expense (move to recycle bin)"""
    user_id = get_current_user_id()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Soft delete: set is_deleted = 1 and deleted_at timestamp
    cursor.execute('''
        UPDATE expenses
        SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP
        WHERE expense_id = ? AND user_id = ?
    ''', (expense_id, user_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Expense not found'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Expense moved to recycle bin'}), 200

# ==================== CATEGORY ROUTES ====================

@app.route('/categories')
@login_required
def categories():
    """Render category management page"""
    return render_template('categories.html')

@app.route('/api/categories', methods=['GET'])
@login_required
def api_get_categories():
    """Get all categories for current user"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.category_id, c.category_name,
               COUNT(e.expense_id) as usage_count
        FROM categories c
        LEFT JOIN expenses e ON c.category_id = e.category_id
        WHERE c.user_id = ?
        GROUP BY c.category_id, c.category_name
        ORDER BY c.category_name
    ''', (user_id,))
    
    categories = [{
        'category_id': row['category_id'],
        'name': row['category_name'],
        'usage_count': row['usage_count']
    } for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({'success': True, 'data': categories}), 200

@app.route('/api/categories', methods=['POST'])
@login_required
def api_add_category():
    """Add a new custom category"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    category_name = data.get('name', '').strip()
    
    if not category_name:
        return jsonify({'success': False, 'message': 'Category name required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO categories (user_id, category_name) VALUES (?, ?)', 
                       (user_id, category_name))
        category_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Category added successfully',
            'category_id': category_id
        }), 201
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': 'Category already exists'}), 400

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
def api_delete_category(category_id):
    """Delete a category"""
    user_id = get_current_user_id()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if category has expenses
    cursor.execute('SELECT COUNT(*) as count FROM expenses WHERE category_id = ?', (category_id,))
    if cursor.fetchone()['count'] > 0:
        conn.close()
        return jsonify({
            'success': False,
            'message': 'Cannot delete category with existing expenses'
        }), 400
    
    cursor.execute('DELETE FROM categories WHERE category_id = ? AND user_id = ?', 
                   (category_id, user_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Category not found'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Category deleted successfully'}), 200

# ==================== REPORTS ROUTES ====================

@app.route('/reports')
@login_required
def reports():
    """Render reports and analytics page"""
    return render_template('reports.html')

@app.route('/api/reports/monthly', methods=['GET'])
@login_required
def api_monthly_report():
    """Get monthly expense report"""
    user_id = get_current_user_id()
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Category-wise breakdown
    cursor.execute('''
        SELECT c.category_name, SUM(e.amount) as total, COUNT(e.expense_id) as count
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
        GROUP BY c.category_name
        ORDER BY total DESC
    ''', (user_id, month))
    
    category_data = [{
        'category': row['category_name'],
        'total': round(row['total'], 2),
        'count': row['count']
    } for row in cursor.fetchall()]
    
    # Payment mode breakdown
    cursor.execute('''
        SELECT payment_mode, SUM(amount) as total, COUNT(*) as count
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
        GROUP BY payment_mode
    ''', (user_id, month))
    
    payment_data = [{
        'mode': row['payment_mode'],
        'total': round(row['total'], 2),
        'count': row['count']
    } for row in cursor.fetchall()]
    
    # Total for the month
    cursor.execute('''
        SELECT SUM(amount) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
    ''', (user_id, month))
    
    total = cursor.fetchone()['total'] or 0
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'month': month,
            'total': round(total, 2),
            'by_category': category_data,
            'by_payment_mode': payment_data
        }
    }), 200

@app.route('/api/reports/daily', methods=['GET'])
@login_required
def api_daily_report():
    """Get daily expense report"""
    user_id = get_current_user_id()
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.expense_id, e.amount, e.payment_mode, e.note,
               c.category_name
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ? AND e.expense_date = ?
        ORDER BY e.created_at DESC
    ''', (user_id, date))
    
    expenses = [{
        'expense_id': row['expense_id'],
        'amount': round(row['amount'], 2),
        'category': row['category_name'],
        'payment_mode': row['payment_mode'],
        'note': row['note'] or ''
    } for row in cursor.fetchall()]
    
    total = sum(exp['amount'] for exp in expenses)
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'date': date,
            'total': round(total, 2),
            'expenses': expenses
        }
    }), 200

@app.route('/api/reports/email-monthly', methods=['POST'])
@login_required
def api_email_monthly_report():
    """Send monthly report via email"""
    from email_report_service import send_monthly_report_email
    
    user_id = get_current_user_id()
    data = request.get_json()
    month = data.get('month', datetime.now().strftime('%Y-%m'))
    
    # Get user info
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, email FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    user_name = user['name']
    user_email = user['email']
    
    # Get monthly report data (reuse existing logic)
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
          AND is_deleted = 0 AND is_draft = 0
    ''', (user_id, month))
    total = cursor.fetchone()['total']
    
    # Category breakdown
    cursor.execute('''
        SELECT c.category_name, SUM(e.amount) as total, COUNT(*) as count
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
          AND e.is_deleted = 0 AND e.is_draft = 0
        GROUP BY c.category_id
        ORDER BY total DESC
    ''', (user_id, month))
    by_category = [{'category': row['category_name'], 'total': round(row['total'], 2), 'count': row['count']} 
                   for row in cursor.fetchall()]
    
    # Payment mode breakdown
    cursor.execute('''
        SELECT payment_mode as mode, SUM(amount) as total, COUNT(*) as count
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
          AND is_deleted = 0 AND is_draft = 0
        GROUP BY payment_mode
        ORDER BY total DESC
    ''', (user_id, month))
    by_payment_mode = [{'mode': row['mode'], 'total': round(row['total'], 2), 'count': row['count']} 
                       for row in cursor.fetchall()]
    
    conn.close()
    
    # Prepare report data
    report_data = {
        'total': round(total, 2),
        'by_category': by_category,
        'by_payment_mode': by_payment_mode
    }
    
    # Send email
    try:
        email_sent = send_monthly_report_email(user_email, user_name, report_data, month)
    except Exception as e:
        print(f"Exception in send_monthly_report_email: {e}")
        import traceback
        traceback.print_exc()
        email_sent = False
    
    # Log audit event
    log_audit(user_id, 'email_report_sent', 'report', None, {'month': month, 'email_sent': email_sent})
    
    if email_sent:
        return jsonify({
            'success': True,
            'message': f'Monthly report sent to {user_email}'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to send email. Please check server logs for details.'
        }), 500

@app.route('/api/reports/download-pdf/<month>', methods=['GET'])
@login_required
def download_monthly_pdf_report(month):
    """Generate and download monthly report as PDF"""
    user_id = session.get('user_id')
    
    # Get user info
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, email FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    user_name = user[0]
    user_email = user[1]
    
    try:
        from pdf_report_generator import generate_monthly_pdf_report
        
        # Generate PDF
        pdf_buffer = generate_monthly_pdf_report(user_id, month, user_name, user_email)
        
        # Prepare filename
        from datetime import datetime
        month_date = datetime.strptime(month, '%Y-%m')
        filename = f"expense_report_{month_date.strftime('%B_%Y')}.pdf"
        
        # Return PDF as download
        from flask import send_file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Error generating PDF report'}), 500

# ==================== BUDGET ROUTES ====================

@app.route('/profile')
@login_required
def profile():
    """Render profile and settings page"""
    return render_template('profile.html')

@app.route('/api/budget', methods=['GET'])
@login_required
def api_get_budget():
    """Get current budget"""
    user_id = get_current_user_id()
    now = datetime.now()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT monthly_limit
        FROM budget
        WHERE user_id = ? AND month = ? AND year = ?
    ''', (user_id, now.month, now.year))
    
    row = cursor.fetchone()
    conn.close()
    
    budget = row['monthly_limit'] if row else 0
    
    return jsonify({'success': True, 'data': {'monthly_limit': budget}}), 200

@app.route('/api/budget', methods=['POST'])
@login_required
def api_set_budget():
    """Set monthly budget"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    monthly_limit = data.get('monthly_limit')
    
    try:
        monthly_limit = float(monthly_limit)
        if monthly_limit <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid budget amount'}), 400
    
    now = datetime.now()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert or update budget
    cursor.execute('''
        INSERT INTO budget (user_id, monthly_limit, month, year)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, month, year)
        DO UPDATE SET monthly_limit = ?
    ''', (user_id, monthly_limit, now.month, now.year, monthly_limit))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Budget updated successfully'}), 200

# ==================== ADVANCED FEATURES ENDPOINTS ====================

# Import advanced API functions
from api_advanced import (
    api_get_accounts, api_create_account, api_update_account, api_delete_account,
    api_get_recurring, api_create_recurring, api_toggle_recurring, api_process_recurring,
    api_copy_expense, api_split_expense, api_get_drafts, api_get_deleted, api_restore_expense,
    api_check_duplicate, api_health_score, api_spending_velocity, api_cost_leaks,
    api_financial_personality, api_spending_heatmap, api_month_comparison,
    api_get_goals, api_create_goal, api_update_goal_progress,
    api_get_challenges, api_create_challenge, api_toggle_favorite, api_get_audit_logs
)

# Accounts Management
@app.route('/accounts')
@login_required
def accounts_page():
    """Render accounts management page"""
    return render_template('accounts.html')

@app.route('/api/accounts', methods=['GET'])
@login_required
def get_accounts():
    return api_get_accounts()

@app.route('/api/accounts', methods=['POST'])
@login_required
def create_account():
    return api_create_account()

@app.route('/api/accounts/<int:account_id>', methods=['PUT'])
@login_required
def update_account(account_id):
    return api_update_account(account_id)

@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_account(account_id):
    return api_delete_account(account_id)

# Recurring Expenses
@app.route('/recurring')
@login_required
def recurring_page():
    """Render recurring expenses page"""
    return render_template('recurring.html')

@app.route('/api/recurring', methods=['GET'])
@login_required
def get_recurring():
    return api_get_recurring()

@app.route('/api/recurring', methods=['POST'])
@login_required
def create_recurring():
    return api_create_recurring()

@app.route('/api/recurring/<int:recurring_id>/toggle', methods=['POST'])
@login_required
def toggle_recurring(recurring_id):
    return api_toggle_recurring(recurring_id)

@app.route('/api/recurring/process', methods=['POST'])
@login_required
def process_recurring():
    return api_process_recurring()

# Advanced Expense Operations
@app.route('/api/expenses/<int:expense_id>/copy', methods=['POST'])
@login_required
def copy_expense(expense_id):
    return api_copy_expense(expense_id)

@app.route('/api/expenses/split', methods=['POST'])
@login_required
def split_expense():
    return api_split_expense()

@app.route('/api/expenses/drafts', methods=['GET'])
@login_required
def get_drafts():
    return api_get_drafts()

@app.route('/api/expenses/deleted', methods=['GET'])
@login_required
def get_deleted():
    return api_get_deleted()

@app.route('/api/expenses/<int:expense_id>/restore', methods=['POST'])
@login_required
def restore_expense(expense_id):
    return api_restore_expense(expense_id)

@app.route('/api/expenses/check-duplicate', methods=['POST'])
@login_required
def check_duplicate():
    return api_check_duplicate()

# Analytics & Insights
@app.route('/analytics')
@login_required
def analytics_page():
    """Render advanced analytics page"""
    return render_template('analytics.html')

@app.route('/api/analytics/health-score', methods=['GET'])
@login_required
def health_score():
    return api_health_score()

@app.route('/api/analytics/velocity', methods=['GET'])
@login_required
def spending_velocity():
    return api_spending_velocity()

@app.route('/api/analytics/cost-leaks', methods=['GET'])
@login_required
def cost_leaks():
    return api_cost_leaks()

@app.route('/api/analytics/personality', methods=['GET'])
@login_required
def financial_personality():
    return api_financial_personality()

@app.route('/api/analytics/heatmap', methods=['GET'])
@login_required
def spending_heatmap():
    return api_spending_heatmap()

@app.route('/api/analytics/comparison', methods=['GET'])
@login_required
def month_comparison():
    return api_month_comparison()

# Goals & Challenges
@app.route('/goals')
@login_required
def goals_page():
    """Render savings goals page"""
    return render_template('goals.html')

@app.route('/api/goals', methods=['GET'])
@login_required
def get_goals():
    return api_get_goals()

@app.route('/api/goals', methods=['POST'])
@login_required
def create_goal():
    return api_create_goal()

@app.route('/api/goals/<int:goal_id>/progress', methods=['POST'])
@login_required
def update_goal_progress(goal_id):
    return api_update_goal_progress(goal_id)

@app.route('/challenges')
@login_required
def challenges_page():
    """Render spending challenges page"""
    return render_template('challenges.html')

@app.route('/api/challenges', methods=['GET'])
@login_required
def get_challenges():
    return api_get_challenges()

@app.route('/api/challenges', methods=['POST'])
@login_required
def create_challenge():
    return api_create_challenge()

# Category Enhancements
@app.route('/api/categories/<int:category_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(category_id):
    return api_toggle_favorite(category_id)

# Audit Logs
@app.route('/api/audit-logs', methods=['GET'])
@login_required
def get_audit_logs():
    return api_get_audit_logs()

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'message': 'Server error'}), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    # Bind to 0.0.0.0 to allow access from other devices on network
    # Access from: http://192.168.180.71:5000
    app.run(debug=True, host='0.0.0.0', port=5000)
