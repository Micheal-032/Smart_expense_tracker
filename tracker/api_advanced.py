"""
Advanced API Endpoints Extension
Additional routes for new features
"""

from flask import request, jsonify
from auth_utils import login_required, get_current_user_id
from database import get_db_connection
from utils import (
    log_audit, create_default_account, update_account_balance,
    calculate_health_score, calculate_spending_velocity,
    detect_cost_leaks, determine_financial_personality,
    check_duplicate_expense, process_recurring_expenses
)
from datetime import datetime, timedelta
import json

# ==================== ACCOUNTS MANAGEMENT ====================

def api_get_accounts():
    """Get all accounts/wallets for user"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT account_id, account_name, balance, currency, is_active
        FROM accounts
        WHERE user_id = ? AND is_active = 1
        ORDER BY account_name
    ''', (user_id,))
    
    accounts = [{ 
        'account_id': row['account_id'],
        'name': row['account_name'],
        'balance': round(row['balance'], 2),
        'currency': row['currency']
    } for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'success': True, 'data': accounts}), 200

def api_create_account():
    """Create new account/wallet"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    account_name = data.get('name', '').strip()
    balance = float(data.get('balance', 0))
    currency = data.get('currency', 'INR')
    
    if not account_name:
        return jsonify({'success': False, 'message': 'Account name required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO accounts (user_id, account_name, balance, currency)
        VALUES (?, ?, ?, ?)
    ''', (user_id, account_name, balance, currency))
    
    account_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    log_audit(user_id, 'CREATE', 'account', account_id)
    
    return jsonify({
        'success': True,
        'message': 'Account created successfully',
        'account_id': account_id
    }), 201

def api_update_account(account_id):
    """Update account details"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute('SELECT account_id FROM accounts WHERE account_id = ? AND user_id = ?',
                   (account_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': 'Account not found'}), 404
    
    account_name = data.get('name')
    balance = data.get('balance')
    
    if account_name:
        cursor.execute('UPDATE accounts SET account_name = ? WHERE account_id = ?',
                      (account_name, account_id))
    
    if balance is not None:
        cursor.execute('UPDATE accounts SET balance = ? WHERE account_id = ?',
                      (float(balance), account_id))
    
    conn.commit()
    conn.close()
    
    log_audit(user_id, 'UPDATE', 'account', account_id)
    
    return jsonify({'success': True, 'message': 'Account updated successfully'}), 200

def api_delete_account(account_id):
    """Soft delete account"""
    user_id = get_current_user_id()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE accounts SET is_active = 0 WHERE account_id = ? AND user_id = ?',
                   (account_id, user_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Account not found'}), 404
    
    conn.commit()
    conn.close()
    
    log_audit(user_id, 'DELETE', 'account', account_id)
    
    return jsonify({'success': True, 'message': 'Account deleted successfully'}), 200

# ==================== RECURRING EXPENSES ====================

def api_get_recurring():
    """Get all recurring expenses"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.recurring_id, r.amount, r.cycle, r.payment_mode, r.note, r.last_added, r.is_active,
               c.category_name
        FROM recurring_expenses r
        JOIN categories c ON r.category_id = c.category_id
        WHERE r.user_id = ?
        ORDER BY r.is_active DESC, r.created_at DESC
    ''', (user_id,))
    
    recurring = [{
        'recurring_id': row['recurring_id'],
        'amount': round(row['amount'], 2),
        'category': row['category_name'],
        'cycle': row['cycle'],
        'payment_mode': row['payment_mode'],
        'note': row['note'] or '',
        'last_added': row['last_added'],
        'is_active': row['is_active'] == 1
    } for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'success': True, 'data': recurring}), 200

def api_create_recurring():
    """Create new recurring expense"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    category_id = data.get('category_id')
    amount = float(data.get('amount'))
    cycle = data.get('cycle')  # daily, weekly, monthly
    payment_mode = data.get('payment_mode')
    note = data.get('note', '').strip()
    
    if cycle not in ['daily', 'weekly', 'monthly']:
        return jsonify({'success': False, 'message': 'Invalid cycle'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO recurring_expenses (user_id, category_id, amount, payment_mode, note, cycle)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, category_id, amount, payment_mode, note, cycle))
    
    recurring_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    log_audit(user_id, 'CREATE', 'recurring_expense', recurring_id)
    
    return jsonify({
        'success': True,
        'message': 'Recurring expense created successfully',
        'recurring_id': recurring_id
    }), 201

def api_toggle_recurring(recurring_id):
    """Toggle recurring expense active/inactive"""
    user_id = get_current_user_id()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE recurring_expenses SET is_active = 1 - is_active WHERE recurring_id = ? AND user_id = ?',
                   (recurring_id, user_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Recurring expense not found'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Updated successfully'}), 200

def api_process_recurring():
    """Manually trigger recurring expense processing"""
    count = process_recurring_expenses()
    return jsonify({
        'success': True,
        'message': f'{count} recurring expense(s) processed'
    }), 200

# ==================== ADVANCED EXPENSE OPERATIONS ====================

def api_copy_expense(expense_id):
    """One-click copy expense"""
    user_id = get_current_user_id()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get original expense
    cursor.execute('''
        SELECT category_id, amount, payment_mode, note
        FROM expenses
        WHERE expense_id = ? AND user_id = ?
    ''', (expense_id, user_id))
    
    expense = cursor.fetchone()
    if not expense:
        conn.close()
        return jsonify({'success': False, 'message': 'Expense not found'}), 404
    
    # Create copy with today's date
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO expenses (user_id, category_id, amount, payment_mode, note, expense_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, expense['category_id'], expense['amount'], expense['payment_mode'],
          expense['note'], today))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    log_audit(user_id, 'COPY', 'expense', new_id, {'from': expense_id})
    
    return jsonify({
        'success': True,
        'message': 'Expense copied successfully',
        'expense_id': new_id
    }), 201

def api_split_expense():
    """Split expense across multiple categories"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    splits = data.get('splits', [])  # [{category_id, amount, note}, ...]
    expense_date = data.get('date')
    payment_mode = data.get('payment_mode')
    
    if not splits or len(splits) < 2:
        return jsonify({'success': False, 'message': 'At least 2 splits required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    expense_ids = []
    for split in splits:
        cursor.execute('''
            INSERT INTO expenses (user_id, category_id, amount, payment_mode, note, expense_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, split['category_id'], split['amount'], payment_mode,
              f"[Split] {split.get('note', '')}", expense_date))
        expense_ids.append(cursor.lastrowid)
    
    conn.commit()
    conn.close()
    
    log_audit(user_id, 'SPLIT', 'expense', None, {'count': len(splits)})
    
    return jsonify({
        'success': True,
        'message': f'Created {len(splits)} split expenses',
        'expense_ids': expense_ids
    }), 201

def api_get_drafts():
    """Get draft expenses"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.expense_id, c.category_name, e.note, e.created_at
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ? AND e.is_draft = 1
        ORDER BY e.created_at DESC
    ''', (user_id,))
    
    drafts = [{
        'expense_id': row['expense_id'],
        'category': row['category_name'],
        'note': row['note'] or '',
        'created_at': row['created_at']
    } for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'success': True, 'data': drafts}), 200

def api_get_deleted():
    """Get recycle bin (soft deleted expenses)"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.expense_id, e.amount, c.category_name, e.expense_date, e.deleted_at
        FROM expenses e
        JOIN categories c ON e.category_id = c.category_id
        WHERE e.user_id = ? AND e.is_deleted = 1
        ORDER BY e.deleted_at DESC
    ''', (user_id,))
    
    deleted = [{
        'expense_id': row['expense_id'],
        'amount': round(row['amount'], 2),
        'category': row['category_name'],
        'date': row['expense_date'],
        'deleted_at': row['deleted_at']
    } for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'success': True, 'data': deleted}), 200

def api_restore_expense(expense_id):
    """Restore expense from recycle bin"""
    user_id = get_current_user_id()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE expenses
        SET is_deleted = 0, deleted_at = NULL
        WHERE expense_id = ? AND user_id = ? AND is_deleted = 1
    ''', (expense_id, user_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Expense not found in recycle bin'}), 404
    
    conn.commit()
    conn.close()
    
    log_audit(user_id, 'RESTORE', 'expense', expense_id)
    
    return jsonify({'success': True, 'message': 'Expense restored successfully'}), 200

def api_check_duplicate():
    """Check for duplicate expense"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    result = check_duplicate_expense(
        user_id,
        float(data.get('amount')),
        data.get('category_id'),
        data.get('date')
    )
    
    return jsonify({'success': True, 'data': result}), 200

# ==================== ANALYTICS & INSIGHTS ====================

def api_health_score():
    """Get financial health score"""
    user_id = get_current_user_id()
    score = calculate_health_score(user_id)
    
    return jsonify({
        'success': True,
        'data': {
            'score': score,
            'rating': 'Excellent' if score >= 80 else 'Good' if score >= 60 else 'Fair' if score >= 40 else 'Poor'
        }
    }), 200

def api_spending_velocity():
    """Get spending velocity analysis"""
    user_id = get_current_user_id()
    velocity = calculate_spending_velocity(user_id)
    
    return jsonify({'success': True, 'data': velocity}), 200

def api_cost_leaks():
    """Detect cost leaks"""
    user_id = get_current_user_id()
    leaks = detect_cost_leaks(user_id)
    
    return jsonify({'success': True, 'data': leaks}), 200

def api_financial_personality():
    """Get financial personality assessment"""
    user_id = get_current_user_id()
    personality = determine_financial_personality(user_id)
    
    return jsonify({'success': True, 'data': personality}), 200

def api_spending_heatmap():
    """Get spending heatmap data for calendar"""
    user_id = get_current_user_id()
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT expense_date, SUM(amount) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
          AND is_deleted = 0 AND is_draft = 0
        GROUP BY expense_date
    ''', (user_id, month))
    
    heatmap = [{
        'date': row['expense_date'],
        'amount': round(row['total'], 2)
    } for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'success': True, 'data': heatmap}), 200

def api_month_comparison():
    """Compare two months"""
    user_id = get_current_user_id()
    month1 = request.args.get('month1')
    month2 = request.args.get('month2')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Month 1 data
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ? AND is_deleted= 0 AND is_draft = 0
    ''', (user_id, month1))
    total1 = cursor.fetchone()['total']
    
    # Month 2 data
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ? AND is_deleted = 0 AND is_draft = 0
    ''', (user_id, month2))
    total2 = cursor.fetchone()['total']
    
    conn.close()
    
    difference = total2 - total1
    percentage_change = (difference / total1 * 100) if total1 > 0 else 0
    
    return jsonify({
        'success': True,
        'data': {
            'month1': {'month': month1, 'total': round(total1, 2)},
            'month2': {'month': month2, 'total': round(total2, 2)},
            'difference': round(difference, 2),
            'percentage_change': round(percentage_change, 2),
            'trend': 'increased' if difference > 0 else 'decreased' if difference < 0 else 'same'
        }
    }), 200

# ==================== GOALS & CHALLENGES ====================

def api_get_goals():
    """Get savings goals"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT goal_id, goal_name, target_amount, current_amount, deadline, is_achieved
        FROM savings_goals
        WHERE user_id = ?
        ORDER BY is_achieved ASC, deadline ASC
    ''', (user_id,))
    
    goals = [{
        'goal_id': row['goal_id'],
        'name': row['goal_name'],
        'target': round(row['target_amount'], 2),
        'current': round(row['current_amount'], 2),
        'percentage': round((row['current_amount'] / row['target_amount'] * 100), 2) if row['target_amount'] > 0 else 0,
        'deadline': row['deadline'],
        'achieved': row['is_achieved'] == 1
    } for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'success': True, 'data': goals}), 200

def api_create_goal():
    """Create new savings goal"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    goal_name = data.get('name', '').strip()
    target_amount = float(data.get('target_amount'))
    deadline = data.get('deadline')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO savings_goals (user_id, goal_name, target_amount, deadline)
        VALUES (?, ?, ?, ?)
    ''', (user_id, goal_name, target_amount, deadline))
    
    goal_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Goal created successfully',
        'goal_id': goal_id
    }), 201

def api_update_goal_progress(goal_id):
    """Update goal progress"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    amount = float(data.get('amount'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE savings_goals
        SET current_amount = current_amount + ?
        WHERE goal_id = ? AND user_id = ?
    ''', (amount, goal_id, user_id))
    
    # Check if goal is achieved
    cursor.execute('''
        UPDATE savings_goals
        SET is_achieved = 1
        WHERE goal_id = ? AND current_amount >= target_amount
    ''', (goal_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Progress updated'}), 200

def api_get_challenges():
    """Get spending challenges"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT challenge_id, challenge_name, daily_limit, start_date, end_date,
               is_active, success_count, fail_count
        FROM spending_challenges
        WHERE user_id = ?
        ORDER BY is_active DESC, created_at DESC
    ''', (user_id,))
    
    challenges = [{
        'challenge_id': row['challenge_id'],
        'name': row['challenge_name'],
        'daily_limit': round(row['daily_limit'], 2),
        'start_date': row['start_date'],
        'end_date': row['end_date'],
        'is_active': row['is_active'] == 1,
        'success_count': row['success_count'],
        'fail_count': row['fail_count']
    } for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'success': True, 'data': challenges}), 200

def api_create_challenge():
    """Create spending challenge"""
    user_id = get_current_user_id()
    data = request.get_json()
    
    challenge_name = data.get('name', '').strip()
    daily_limit = float(data.get('daily_limit'))
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO spending_challenges (user_id, challenge_name, daily_limit, start_date, end_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, challenge_name, daily_limit, start_date, end_date))
    
    challenge_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Challenge created successfully',
        'challenge_id': challenge_id
    }), 201

# ==================== CATEGORY ENHANCEMENTS ====================

def api_toggle_favorite(category_id):
    """Toggle category favorite status"""
    user_id = get_current_user_id()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE categories
        SET is_favorite = 1 - is_favorite
        WHERE category_id = ? AND user_id = ?
    ''', (category_id, user_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'success': False, 'message': 'Category not found'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Favorite status updated'}), 200

# ==================== AUDIT LOGS ====================

def api_get_audit_logs():
    """Get audit trail"""
    user_id = get_current_user_id()
    limit = request.args.get('limit', 50, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT log_id, action, entity, entity_id, details, timestamp
        FROM audit_logs
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (user_id, limit))
    
    logs = [{
        'log_id': row['log_id'],
        'action': row['action'],
        'entity': row['entity'],
        'entity_id': row['entity_id'],
        'details': json.loads(row['details']) if row['details'] else None,
        'timestamp': row['timestamp']
    } for row in cursor.fetchall()]
    
    conn.close()
    return jsonify({'success': True, 'data': logs}), 200
