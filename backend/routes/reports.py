"""Reports routes - PDF generation."""
import os
from io import BytesIO
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Blueprint, session, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

from database.db import get_db
from services.analytics import get_session_dates, compute_streak
from utils.response import error_response

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return error_response('Authentication required', 401)
        return f(*args, **kwargs)
    return decorated


@reports_bp.route('/weekly-pdf', methods=['GET'])
@login_required
def weekly_pdf():
    """Download weekly PDF report."""
    conn = get_db()
    user_id = session['user_id']
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())

    rows = conn.execute('''
        SELECT subject, SUM(duration_minutes) as total
        FROM study_sessions
        WHERE user_id = ? AND date(start_time) >= ? AND duration_minutes > 0
        GROUP BY subject
    ''', (user_id, week_start.isoformat())).fetchall()

    total_minutes = sum(r['total'] for r in rows)
    dates = get_session_dates(conn, user_id, days=7)
    streak = compute_streak(dates)
    conn.close()

    subjects = [r['subject'] for r in rows]
    minutes = [r['total'] for r in rows]

    chart_buffer = BytesIO()
    if subjects:
        plt.figure(figsize=(4, 4))
        plt.pie(minutes, labels=subjects, autopct='%1.1f%%')
        plt.title("Study Time Distribution")
        plt.tight_layout()
        plt.savefig(chart_buffer, format='png')
        plt.close()
        chart_buffer.seek(0)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, fontSize=18)
    story = []

    logo_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'images', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1 * inch, height=1 * inch)
        logo.hAlign = "CENTER"
        story.append(logo)

    story.append(Spacer(1, 15))
    story.append(Paragraph("Smart Study Focus Tracker", title_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph("Weekly Study Analytics Report", styles['Heading2']))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Student: {session.get('username', 'User')}", styles['Normal']))
    story.append(Paragraph(
        f"Week: {week_start.strftime('%B %d, %Y')} - {today.strftime('%B %d, %Y')}",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"<b>Total Study Time:</b> {total_minutes} minutes ({total_minutes/60:.1f} hours)",
        styles['Normal']
    ))
    story.append(Paragraph(
        f"<b>Current Study Streak:</b> {streak} day(s)",
        styles['Normal']
    ))
    story.append(Spacer(1, 25))

    if rows:
        table_data = [['Subject', 'Minutes']]
        for r in rows:
            table_data.append([r['subject'], str(r['total'])])
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No sessions recorded this week.", styles['Normal']))

    if subjects:
        story.append(Spacer(1, 25))
        story.append(Paragraph("Study Time Distribution", styles['Heading2']))
        story.append(Spacer(1, 10))
        chart_image = Image(chart_buffer, width=2.5 * inch, height=2.5 * inch)
        chart_image.hAlign = "CENTER"
        story.append(chart_image)

    doc.build(story)
    buffer.seek(0)
    filename = f'weekly-report-{week_start.strftime("%Y-%m-%d")}.pdf'
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)
