"""
PDF Report Generator Module

Generates professional PDF reports for monthly expense data
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import io
from datetime import datetime
from database import get_db_connection

# App colors
PRIMARY_COLOR = colors.HexColor('#667eea')
SECONDARY_COLOR = colors.HexColor('#764ba2')
ACCENT_COLOR = colors.HexColor('#ffc107')
TEXT_COLOR = colors.HexColor('#333333')
LIGHT_GRAY = colors.HexColor('#f5f5f5')


class NumberedCanvas(canvas.Canvas):
    """Custom canvas for adding headers and footers"""
    
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
        page_num = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 0.75*inch, 0.5*inch, page_num)
        self.drawString(0.75*inch, 0.5*inch, "Expense Tracker Report")


def create_pie_chart(data, title):
    """Create a pie chart and return as image buffer"""
    fig, ax = plt.subplots(figsize=(6, 4))
    
    labels = [item['label'] for item in data[:8]]  # Top 8
    sizes = [item['value'] for item in data[:8]]
    colors_list = ['#667eea', '#764ba2', '#ffc107', '#4CAF50', '#FF5722', '#2196F3', '#9C27B0', '#FF9800']
    
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors_list, startangle=90)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf


def create_line_chart(data, title, xlabel, ylabel):
    """Create a line chart and return as image buffer"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    x_values = [item['label'] for item in data]
    y_values = [item['value'] for item in data]
    
    ax.plot(x_values, y_values, color='#667eea', linewidth=2, marker='o', markersize=4)
    ax.fill_between(range(len(x_values)), y_values, alpha=0.3, color='#667eea')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    
    # Rotate x-axis labels if too many
    if len(x_values) > 10:
        plt.xticks(rotation=45, ha='right')
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf


def generate_monthly_pdf_report(user_id, month_str, user_name, user_email):
    """
    Generate comprehensive monthly PDF report
    
    Args:
        user_id: User ID
        month_str: Month string (e.g., "2026-02")
        user_name: User's name
        user_email: User's email
    
    Returns:
        BytesIO: PDF file buffer
    """
    
    # Create PDF buffer
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=PRIMARY_COLOR,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=SECONDARY_COLOR,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.leading = 14
    
    # Fetch data from database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get month name
    month_date = datetime.strptime(month_str, '%Y-%m')
    month_name = month_date.strftime('%B %Y')
    
    # Get total spending
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
    ''', (user_id, month_str))
    total_row = cursor.fetchone()
    total_spending = total_row[0]
    total_transactions = total_row[1]
    
    # Get category breakdown
    cursor.execute('''
        SELECT c.category_name, COALESCE(SUM(e.amount), 0) as total, COUNT(e.expense_id) as count
        FROM categories c
        LEFT JOIN expenses e ON c.category_id = e.category_id AND e.user_id = ? AND strftime('%Y-%m', e.expense_date) = ?
        WHERE c.user_id = ?
        GROUP BY c.category_id, c.category_name
        HAVING total > 0
        ORDER BY total DESC
    ''', (user_id, month_str, user_id))
    categories = cursor.fetchall()
    
    # Get payment mode breakdown
    cursor.execute('''
        SELECT payment_mode, COALESCE(SUM(amount), 0) as total, COUNT(*) as count
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
        GROUP BY payment_mode
        ORDER BY total DESC
    ''', (user_id, month_str))
    payment_modes = cursor.fetchall()
    
    # Get daily spending
    cursor.execute('''
        SELECT expense_date, COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE user_id = ? AND strftime('%Y-%m', expense_date) = ?
        GROUP BY expense_date
        ORDER BY expense_date
    ''', (user_id, month_str))
    daily_spending = cursor.fetchall()
    
    conn.close()
    
    # ==================== COVER PAGE ====================
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("💰 Expense Tracker", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    cover_info_style = ParagraphStyle(
        'CoverInfo',
        parent=styles['Normal'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=8
    )
    
    elements.append(Paragraph(f"<b>Monthly Expense Report</b>", cover_info_style))
    elements.append(Paragraph(f"{month_name}", cover_info_style))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Prepared for: {user_name}", cover_info_style))
    elements.append(Paragraph(f"{user_email}", cover_info_style))
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", cover_info_style))
    
    elements.append(PageBreak())
    
    # ==================== EXECUTIVE SUMMARY ====================
    elements.append(Paragraph("Executive Summary", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Summary box
    summary_data = [
        ['Total Spending', f'Rs. {total_spending:,.2f}'],
        ['Total Transactions', str(total_transactions)],
        ['Average per Transaction', f'Rs. {(total_spending/total_transactions if total_transactions > 0 else 0):,.2f}'],
        ['Average per Day', f'Rs. {(total_spending/30):,.2f}'],
        ['Top Category', categories[0][0] if categories else 'N/A']
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('TEXTCOLOR', (0, 0), (-1, -1), TEXT_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.white)
    ]))
    
    elements.append(summary_table)
    elements.append(PageBreak())
    
    # ==================== CATEGORY BREAKDOWN ====================
    elements.append(Paragraph("Spending by Category", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    if categories:
        # Category table
        category_data = [['Category', 'Amount', 'Transactions', 'Percentage']]
        for cat in categories:
            percentage = (cat[1] / total_spending * 100) if total_spending > 0 else 0
            category_data.append([
                cat[0],
                f'Rs. {cat[1]:,.2f}',
                str(cat[2]),
                f'{percentage:.1f}%'
            ])
        
        category_table = Table(category_data, colWidths=[2.5*inch, 1.5*inch, 1.2*inch, 1*inch])
        category_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY])
        ]))
        
        elements.append(category_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Category pie chart
        chart_data = [{'label': cat[0], 'value': cat[1]} for cat in categories]
        pie_chart_buf = create_pie_chart(chart_data, 'Category Distribution')
        pie_chart_img = Image(pie_chart_buf, width=5*inch, height=3.3*inch)
        elements.append(pie_chart_img)
    else:
        elements.append(Paragraph("No expenses recorded for this month.", normal_style))
    
    elements.append(PageBreak())
    
    # ==================== PAYMENT METHODS ====================
    elements.append(Paragraph("Payment Methods", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    if payment_modes:
        payment_data = [['Payment Method', 'Amount', 'Transactions', 'Percentage']]
        for mode in payment_modes:
            percentage = (mode[1] / total_spending * 100) if total_spending > 0 else 0
            payment_data.append([
                mode[0],
                f'Rs. {mode[1]:,.2f}',
                str(mode[2]),
                f'{percentage:.1f}%'
            ])
        
        payment_table = Table(payment_data, colWidths=[2.5*inch, 1.5*inch, 1.2*inch, 1*inch])
        payment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), SECONDARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY])
        ]))
        
        elements.append(payment_table)
    else:
        elements.append(Paragraph("No payment data available.", normal_style))
    
    elements.append(PageBreak())
    
    # ==================== DAILY SPENDING TREND ====================
    elements.append(Paragraph("Daily Spending Trend", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    if daily_spending:
        chart_data = [{'label': row[0][-2:], 'value': row[1]} for row in daily_spending]  # Use day only
        line_chart_buf = create_line_chart(chart_data, f'Daily Spending - {month_name}', 'Day', 'Amount (Rs.)')
        line_chart_img = Image(line_chart_buf, width=6.5*inch, height=3.5*inch)
        elements.append(line_chart_img)
    else:
        elements.append(Paragraph("No daily spending data available.", normal_style))
    
    elements.append(PageBreak())
    
    # ==================== INSIGHTS & RECOMMENDATIONS ====================
    elements.append(Paragraph("Insights & Recommendations", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    insights = []
    
    if total_transactions > 0:
        avg_transaction = total_spending / total_transactions
        insights.append(f"• You made {total_transactions} transactions this month with an average of Rs. {avg_transaction:,.2f} per transaction.")
    
    if categories:
        top_category = categories[0]
        top_percentage = (top_category[1] / total_spending * 100) if total_spending > 0 else 0
        insights.append(f"• Your highest spending category was <b>{top_category[0]}</b>, accounting for {top_percentage:.1f}% (Rs. {top_category[1]:,.2f}) of total expenses.")
    
    if len(categories) >= 3:
        top_3_total = sum(cat[1] for cat in categories[:3])
        top_3_percentage = (top_3_total / total_spending * 100) if total_spending > 0 else 0
        insights.append(f"• Your top 3 categories represent {top_3_percentage:.1f}% of your total spending.")
    
    if daily_spending:
        daily_amounts = [row[1] for row in daily_spending]
        max_day = max(daily_amounts)
        avg_day = sum(daily_amounts) / len(daily_amounts)
        insights.append(f"• Your highest spending day was Rs. {max_day:,.2f}, while your average daily spending was Rs. {avg_day:,.2f}.")
    
    insights.append(f"• Total spending for {month_name}: Rs. {total_spending:,.2f}")
    
    for insight in insights:
        elements.append(Paragraph(insight, normal_style))
        elements.append(Spacer(1, 0.15*inch))
    
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Recommendations:</b>", normal_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("• Review your top spending categories to identify potential savings opportunities.", normal_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("• Set monthly budgets for high-expense categories to better control spending.", normal_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph("• Track recurring expenses and consider alternatives or negotiations for better rates.", normal_style))
    
    # Build PDF
    doc.build(elements, canvasmaker=NumberedCanvas)
    
    # Get PDF data
    buffer.seek(0)
    return buffer
