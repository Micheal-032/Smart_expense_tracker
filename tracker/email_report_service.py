"""
Email Report Service Module

Handles formatting and sending monthly expense reports via email
"""

from email_service import EMAIL_SERVICE_API_KEY, APP_URL
from datetime import datetime

def format_monthly_report_email(report_data, user_name, month_str):
    """
    Format monthly report data into beautiful HTML email
    
    Args:
        report_data: Report data from /api/reports/monthly
        user_name: User's name
        month_str: Month string (e.g., "2026-02")
    
    Returns:
        tuple: (subject, html_body, text_body)
    """
    
    # Parse month
    try:
        date_obj = datetime.strptime(month_str, '%Y-%m')
        month_name = date_obj.strftime('%B %Y')
    except:
        month_name = month_str
    
    # Calculate percentages for categories
    total = report_data.get('total', 0)
    categories = report_data.get('by_category', [])
    payment_modes = report_data.get('by_payment_mode', [])
    
    # Generate category table rows
    category_rows = ''
    for cat in categories[:10]:  # Top 10 categories
        amount = cat.get('total', 0)
        percentage = (amount / total * 100) if total > 0 else 0
        count = cat.get('count', 0)
        category_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #eee;">{cat.get('category', 'Unknown')}</td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right; font-weight: 600;">Rs. {amount:,.2f}</td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">{count}</td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">{percentage:.1f}%</td>
        </tr>
        """
    
    # Generate payment mode rows
    payment_rows = ''
    for mode in payment_modes:
        amount = mode.get('total', 0)
        percentage = (amount / total * 100) if total > 0 else 0
        count = mode.get('count', 0)
        payment_rows += f"""
        <tr>
            <td style="padding: 12px; border-bottom: 1px solid #eee;">{mode.get('mode', 'Unknown')}</td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right; font-weight: 600;">Rs. {amount:,.2f}</td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">{count}</td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">{percentage:.1f}%</td>
        </tr>
        """
    
    # Email subject
    subject = f'Your Monthly Expense Report - {month_name}'
    
    # HTML body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Monthly Expense Report</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5;">
        <div style="max-width: 650px; margin: 0 auto; background: white;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; color: white;">
                <h1 style="margin: 0; font-size: 32px; font-weight: 700;">Expense Tracker</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.95;">Monthly Expense Report</p>
                <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: 600;">{month_name}</p>
            </div>
            
            <!-- Greeting -->
            <div style="padding: 30px;">
                <p style="margin: 0 0 20px 0; font-size: 16px; color: #333;">Hello <strong>{user_name}</strong>,</p>
                <p style="margin: 0 0 30px 0; font-size: 16px; color: #666; line-height: 1.6;">
                    Here's your comprehensive expense report for {month_name}. Below you'll find a detailed breakdown of your spending.
                </p>
                
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 12px; margin-bottom: 30px;">
                    <h2 style="margin: 0 0 15px 0; color: white; font-size: 20px;">Summary</h2>
                    <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; backdrop-filter: blur(10px);">
                        <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 14px;">Total Spending</p>
                        <p style="margin: 5px 0 0 0; color: white; font-size: 36px; font-weight: 700;">Rs. {total:,.2f}</p>
                    </div>
                </div>
                
                <!-- Category Breakdown -->
                <div style="margin-bottom: 30px;">
                    <h2 style="margin: 0 0 20px 0; color: #333; font-size: 20px; border-bottom: 3px solid #667eea; padding-bottom: 10px;">
                        Spending by Category
                    </h2>
                    <table style="width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 15px 12px; text-align: left; font-weight: 600; color: #666; font-size: 14px; border-bottom: 2px solid #667eea;">Category</th>
                                <th style="padding: 15px 12px; text-align: right; font-weight: 600; color: #666; font-size: 14px; border-bottom: 2px solid #667eea;">Amount</th>
                                <th style="padding: 15px 12px; text-align: center; font-weight: 600; color: #666; font-size: 14px; border-bottom: 2px solid #667eea;">Count</th>
                                <th style="padding: 15px 12px; text-align: right; font-weight: 600; color: #666; font-size: 14px; border-bottom: 2px solid #667eea;">%</th>
                            </tr>
                        </thead>
                        <tbody>
                            {category_rows if category_rows else '<tr><td colspan="4" style="padding: 20px; text-align: center; color: #999;">No expenses this month</td></tr>'}
                        </tbody>
                    </table>
                </div>
                
                <!-- Payment Mode Breakdown -->
                <div style="margin-bottom: 30px;">
                    <h2 style="margin: 0 0 20px 0; color: #333; font-size: 20px; border-bottom: 3px solid #764ba2; padding-bottom: 10px;">
                        Payment Methods
                    </h2>
                    <table style="width: 100%; border-collapse: collapse; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">
                        <thead>
                            <tr style="background: #f8f9fa;">
                                <th style="padding: 15px 12px; text-align: left; font-weight: 600; color: #666; font-size: 14px; border-bottom: 2px solid #764ba2;">Payment Mode</th>
                                <th style="padding: 15px 12px; text-align: right; font-weight: 600; color: #666; font-size: 14px; border-bottom: 2px solid #764ba2;">Amount</th>
                                <th style="padding: 15px 12px; text-align: center; font-weight: 600; color: #666; font-size: 14px; border-bottom: 2px solid #764ba2;">Count</th>
                                <th style="padding: 15px 12px; text-align: right; font-weight: 600; color: #666; font-size: 14px; border-bottom: 2px solid #764ba2;">%</th>
                            </tr>
                        </thead>
                        <tbody>
                            {payment_rows if payment_rows else '<tr><td colspan="4" style="padding: 20px; text-align: center; color: #999;">No transactions</td></tr>'}
                        </tbody>
                    </table>
                </div>
                
                <!-- Insights -->
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; border-radius: 4px; margin-bottom: 30px;">
                    <p style="margin: 0; color: #856404; font-size: 16px; font-weight: 600;">Quick Insight</p>
                    <p style="margin: 10px 0 0 0; color: #856404; font-size: 14px; line-height: 1.6;">
                        {'You spent Rs. {:,.2f} this month across {} transactions. Keep tracking to improve your financial health!'.format(total, sum(cat.get('count', 0) for cat in categories))}
                    </p>
                </div>
                
                <!-- Call to Action -->
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{APP_URL}/api/reports/download-pdf/{month_str}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);">
                        Download Full PDF Report
                    </a>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background: #f8f9fa; padding: 25px 30px; border-top: 1px solid #dee2e6; text-align: center;">
                <p style="margin: 0 0 10px 0; color: #999; font-size: 12px;">
                    This report was automatically generated by Smart Expense Tracker
                </p>
                <p style="margin: 0; color: #999; font-size: 12px;">
                    © {datetime.now().year} Expense Tracker. All rights reserved.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    
    MONTHLY EXPENSE REPORT - {month_name}
    =====================================
    
    Hello {user_name},
    
    Here's your expense report for {month_name}:
    
    SUMMARY
    -------
    Total Spending: Rs. {total:,.2f}
    
    CATEGORY BREAKDOWN
    ------------------
    """
    
    for cat in categories[:10]:
        amount = cat.get('total', 0)
        percentage = (amount / total * 100) if total > 0 else 0
        count = cat.get('count', 0)
        text_body += f"\n{cat.get('category', 'Unknown')}: Rs. {amount:,.2f} ({count} txn, {percentage:.1f}%)"
    
    text_body += f"""
    
    PAYMENT METHODS
    ---------------
    """
    
    for mode in payment_modes:
        amount = mode.get('total', 0)
        count = mode.get('count', 0)
        text_body += f"\n{mode.get('mode', 'Unknown')}: Rs. {amount:,.2f} ({count} txn)"
    
    text_body += f"""
    
    View detailed reports at: {APP_URL}/reports
    
    — Expense Tracker Team
    """
    
    return subject, html_body, text_body


def send_monthly_report_email(user_email, user_name, report_data, month_str):
    """
    Send monthly report via email
    
    Args:
        user_email: User's email address
        user_name: User's name
        report_data: Report data from API
        month_str: Month string (YYYY-MM)
    
    Returns:
        bool: True if sent successfully
    """
    
    try:
        subject, html_body, text_body = format_monthly_report_email(report_data, user_name, month_str)
        
        # For development, log the email
        print(f"\n{'='*70}")
        print("SENDING MONTHLY REPORT EMAIL:")
        print(f"{'='*70}")
        print(f"To: {user_email}")
        print(f"Subject: {subject}")
        print(f"Month: {month_str}")
        print(f"Total Spending: Rs. {report_data.get('total', 0):,.2f}")
        print(f"{'='*70}\n")
        
        # Actually send the email using Antigravity API
        try:
            import requests
            
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {EMAIL_SERVICE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "Expense Tracker <onboarding@resend.dev>",
                    "to": [user_email],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body
                }
            )
            
            if response.status_code == 200:
                print(f"[SUCCESS] Email sent successfully to {user_email}")
                return True
            else:
                print(f"[ERROR] Email failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error calling email API: {e}")
            return False
        
    except Exception as e:
        print(f"Error sending report email: {e}")
        return False
