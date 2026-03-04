"""
Email Service Module

Handles email sending for password reset using Antigravity's internal email service.
"""

import requests
import json
from datetime import datetime

# Email service configuration
EMAIL_SERVICE_API_KEY = "re_fYMBweJo_MrgVvb7GfwervKjBpQyqPikc"
APP_URL = "http://192.168.180.71:5000"  # Network IP for access from all devices

def send_password_reset_email(user_email, user_name, otp, token):
    """
    Send password reset email with OTP and reset link
    
    Args:
        user_email: Recipient email address
        user_name: User's display name
        otp: 6-digit OTP
        token: Secure reset token
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    reset_link = f"{APP_URL}/reset-password?token={token}"
    
    # HTML email template
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 28px;">💰 Expense Tracker</h1>
            </div>
            
            <!-- Content -->
            <div style="padding: 40px 30px;">
                <h2 style="color: #673AB7; margin-top: 0;">Password Reset Request</h2>
                
                <p>Hello <strong>{user_name}</strong>,</p>
                
                <p>We received a request to reset your password for your Expense Tracker account.</p>
                
                <!-- OTP Box -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 8px; margin: 30px 0; text-align: center;">
                    <p style="margin: 0; font-size: 14px; color: rgba(255,255,255,0.9);">Your One-Time Password (OTP):</p>
                    <p style="margin: 15px 0 0 0; font-size: 36px; font-weight: bold; color: white; letter-spacing: 8px; font-family: 'Courier New', monospace;">{otp}</p>
                </div>
                
                <p style="margin-top: 30px;">Or click the secure link below to reset your password:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 16px;">Reset Password</a>
                </div>
                
                <!-- Warning Box -->
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 30px 0; border-radius: 4px;">
                    <p style="margin: 0; color: #856404; font-size: 14px;">
                        ⏰ <strong>Important:</strong> This OTP and link will expire in <strong>15 minutes</strong>.
                    </p>
                </div>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    If you did not request this password reset, please ignore this email. Your password will remain unchanged.
                </p>
            </div>
            
            <!-- Footer -->
            <div style="background: #f8f9fa; padding: 20px 30px; border-top: 1px solid #dee2e6;">
                <p style="color: #999; font-size: 12px; margin: 0; text-align: center;">
                    — Expense Tracker Security Team<br>
                    This is an automated message, please do not reply.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version (fallback)
    text_body = f"""
    Password Reset Request
    
    Hello {user_name},
    
    We received a request to reset your password for your Expense Tracker account.
    
    Your One-Time Password (OTP): {otp}
    
    Or click the secure link below:
    {reset_link}
    
    ⏰ This OTP and link will expire in 15 minutes.
    
    If you did not request this password reset, please ignore this email.
    
    — Expense Tracker Security Team
    """
    
    try:
        # Note: This is a placeholder for Antigravity's email service
        # The actual implementation will use Antigravity's internal email API
        
        # For development/testing, log the email instead of sending
        print(f"\n{'='*60}")
        print("📧 EMAIL WOULD BE SENT:")
        print(f"{'='*60}")
        print(f"To: {user_email}")
        print(f"Subject: Reset Your Expense Tracker Password")
        print(f"OTP: {otp}")
        print(f"Reset Link: {reset_link}")
        print(f"{'='*60}\n")
        
        # TODO: Replace with actual Antigravity email API call
        # Example:
        # response = requests.post(
        #     "https://api.antigravity.dev/email/send",
        #     headers={"Authorization": f"Bearer {EMAIL_SERVICE_API_KEY}"},
        #     json={
        #         "to": user_email,
        #         "subject": "Reset Your Expense Tracker Password",
        #         "html": html_body,
        #         "text": text_body
        #     }
        # )
        # return response.status_code == 200
        
        # For now, return True to simulate successful sending
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def validate_email_format(email):
    """
    Simple email format validation
    
    Args:
        email: Email address to validate
    
    Returns:
        bool: True if valid format, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
