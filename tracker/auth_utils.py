"""
Authentication utilities for Smart Personal Expense Tracker
Handles password hashing, verification, and session management
"""

from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, url_for, jsonify
import re

def hash_password(password):
    """Hash a password using werkzeug's secure method"""
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(password_hash, password):
    """Verify a password against its hash"""
    return check_password_hash(password_hash, password)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Validate password strength
    Requirements: At least 8 characters, contains letter and number
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # For API routes, return JSON error
            if '/api/' in str(f):
                return jsonify({'success': False, 'message': 'Login required'}), 401
            # For page routes, redirect to login
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    """Get the current logged-in user's ID from session"""
    return session.get('user_id')

def set_current_user(user_id, email, name):
    """Set the current user in session"""
    session['user_id'] = user_id
    session['email'] = email
    session['name'] = name

def clear_session():
    """Clear the current user session"""
    session.clear()
