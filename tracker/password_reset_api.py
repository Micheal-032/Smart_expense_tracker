"""
Password Reset API Module

Handles all password reset logic including token generation, validation, and password updates.
"""

import sqlite3
import secrets
import hashlib
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from email_service import send_password_reset_email
from utils import log_audit
from database import get_db_connection

# Removed local get_db_connection - now using shared one from database.py


def generate_reset_token(user_id):
    """
    Generate secure reset token using SHA256
    
    Args:
        user_id: User ID to include in token
    
    Returns:
        str: Secure token hash
    """
    random_component = secrets.token_urlsafe(32)
    timestamp = str(datetime.now().timestamp())
    data = f"{random_component}{timestamp}{user_id}"
    return hashlib.sha256(data.encode()).hexdigest()


def generate_otp():
    """
    Generate 6-digit OTP
    
    Returns:
        str: 6-digit numeric OTP
    """
    return str(random.randint(100000, 999999))


def check_reset_rate_limit(user_id):
    """
    Check if user has exceeded rate limit (3 requests per hour)
    
    Args:
        user_id: User ID to check
    
    Returns:
        bool: True if under limit, False if exceeded
    """
    conn = get_db_connection()
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    count = conn.execute('''
        SELECT COUNT(*) as count FROM password_resets
        WHERE user_id = ? AND created_at > ?
    ''', (user_id, one_hour_ago)).fetchone()['count']
    
    conn.close()
    return count < 3


def create_password_reset_request(email):
    """
    Create a password reset request
    
    Args:
        email: User's email address
    
    Returns:
        dict: Result with success status and message
    """
    conn = get_db_connection()
    
    try:
        # Check if user exists
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        # Always return generic message to prevent email enumeration
        generic_message = "If this email exists, a reset link has been sent."
        
        if not user:
            return {'success': True, 'message': generic_message}
        
        user_id = user['user_id']
        user_name = user['name']  # Fixed: column is 'name' not 'username'
        
        # Check rate limit
        if not check_reset_rate_limit(user_id):
            return {
                'success': False,
                'message': 'Too many reset requests. Please try again later.'
            }
        
        # Generate token and OTP
        token = generate_reset_token(user_id)
        otp = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=15)
        
        # Store in database
        conn.execute('''
            INSERT INTO password_resets (user_id, token, otp, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, token, otp, expires_at))
        conn.commit()
        
        # Send email
        email_sent = send_password_reset_email(email, user_name, otp, token)
        
        # Log audit event
        log_audit(user_id, 'password_reset_requested', 'user', user_id, {
            'email': email,
            'email_sent': email_sent
        })
        
        return {'success': True, 'message': generic_message}
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating password reset: {e}")
        return {'success': False, 'message': 'An error occurred. Please try again.'}
        
    finally:
        conn.close()


def validate_reset_token(token, otp):
    """
    Validate reset token and OTP
    
    Args:
        token: Reset token
        otp: One-time password
    
    Returns:
        dict: Result with success status, message, and user_id if valid
    """
    conn = get_db_connection()
    
    try:
        # Find reset record
        reset_record = conn.execute('''
            SELECT * FROM password_resets
            WHERE token = ? AND is_used = 0
        ''', (token,)).fetchone()
        
        if not reset_record:
            return {'success': False, 'message': 'Invalid or expired reset link.'}
        
        # Check expiry
        expires_at = datetime.fromisoformat(reset_record['expires_at'])
        if datetime.now() > expires_at:
            return {'success': False, 'message': 'This reset link has expired.'}
        
        # Validate OTP
        if reset_record['otp'] != otp:
            # Log failed attempt
            log_audit(reset_record['user_id'], 'password_reset_failed', 'user', 
                     reset_record['user_id'], {'reason': 'invalid_otp'})
            return {'success': False, 'message': 'Invalid OTP. Please check and try again.'}
        
        return {
            'success': True,
            'user_id': reset_record['user_id'],
            'reset_id': reset_record['reset_id']
        }
        
    finally:
        conn.close()


def update_user_password(user_id, reset_id, new_password):
    """
    Update user's password and mark reset as used
    
    Args:
        user_id: User ID
        reset_id: Password reset record ID
        new_password: New password (plain text, will be hashed)
    
    Returns:
        dict: Result with success status and message
    """
    conn = get_db_connection()
    
    try:
        # Hash new password
        password_hash = generate_password_hash(new_password)
        
        # Update user's password
        conn.execute('''
            UPDATE users
            SET password_hash = ?
            WHERE user_id = ?
        ''', (password_hash, user_id))
        
        # Mark reset as used
        conn.execute('''
            UPDATE password_resets
            SET is_used = 1
            WHERE reset_id = ?
        ''', (reset_id,))
        
        conn.commit()
        
        # Log successful reset
        log_audit(user_id, 'password_reset_completed', 'user', user_id, {
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'success': True,
            'message': 'Password updated successfully. Please log in with your new password.'
        }
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating password: {e}")
        return {'success': False, 'message': 'Failed to update password. Please try again.'}
        
    finally:
        conn.close()


def cleanup_expired_resets():
    """
    Delete expired password reset records (older than 24 hours)
    
    Returns:
        int: Number of records deleted
    """
    conn = get_db_connection()
    
    try:
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        cursor = conn.execute('''
            DELETE FROM password_resets
            WHERE expires_at < ?
        ''', (cutoff_time,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} expired password reset record(s)")
        
        return deleted_count
        
    except Exception as e:
        conn.rollback()
        print(f"Error cleaning up expired resets: {e}")
        return 0
        
    finally:
        conn.close()
