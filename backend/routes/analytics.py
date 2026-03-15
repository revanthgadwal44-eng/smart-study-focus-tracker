"""Analytics routes - all queries filter by user_id."""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, session

from database.db import get_db
from services.analytics import get_session_dates, compute_streak
from utils.response import success_response, error_response

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return error_response('Authentication required', 401)
        return f(*args, **kwargs)
    return decorated


def _user_id():
    return session['user_id']


@analytics_bp.route('/daily', methods=['GET'])
@login_required
def daily():
    """Today's study minutes."""
    conn = get_db()
    today = datetime.now(timezone.utc).date().isoformat()
    row = conn.execute('''
        SELECT COALESCE(SUM(duration_minutes), 0) as total
        FROM study_sessions
        WHERE user_id = ? AND date(start_time) = ? AND duration_minutes > 0
    ''', (_user_id(), today)).fetchone()
    conn.close()
    return success_response({'total_minutes': row['total'], 'date': today})


@analytics_bp.route('/weekly', methods=['GET'])
@login_required
def weekly():
    """Weekly hours and subject totals."""
    conn = get_db()
    today = datetime.now(timezone.utc).date()
    week_start = today - timedelta(days=today.weekday())

    rows = conn.execute('''
        SELECT subject, SUM(duration_minutes) as total
        FROM study_sessions
        WHERE user_id = ? AND date(start_time) >= ? AND duration_minutes > 0
        GROUP BY subject
    ''', (_user_id(), week_start.isoformat())).fetchall()

    total = sum(r['total'] for r in rows)
    by_subject = {r['subject']: r['total'] for r in rows}
    conn.close()
    return success_response({
        'total_minutes': total,
        'by_subject': by_subject,
        'week_start': week_start.isoformat()
    })


@analytics_bp.route('/streak', methods=['GET'])
@login_required
def streak():
    """Consecutive days with study sessions."""
    conn = get_db()
    dates = get_session_dates(conn, _user_id(), days=365)
    s = compute_streak(dates)
    conn.close()
    return success_response({'streak': s})


@analytics_bp.route('/weekly-progress', methods=['GET'])
@login_required
def weekly_progress():
    """Mon-Sun minutes for current week."""
    conn = get_db()
    today = datetime.now(timezone.utc).date()
    week_start = today - timedelta(days=today.weekday())

    days_out = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        row = conn.execute('''
            SELECT COALESCE(SUM(duration_minutes), 0) as total
            FROM study_sessions
            WHERE user_id = ? AND date(start_time) = ? AND duration_minutes > 0
        ''', (_user_id(), d.isoformat())).fetchone()
        days_out.append({
            'day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i],
            'date': d.isoformat(),
            'minutes': row['total'],
            'is_today': d == today
        })
    conn.close()
    return success_response({'days': days_out})


@analytics_bp.route('/subject-breakdown', methods=['GET'])
@login_required
def subject_breakdown():
    """Subject-wise totals for today."""
    conn = get_db()
    today = datetime.now(timezone.utc).date().isoformat()
    rows = conn.execute('''
        SELECT subject, SUM(duration_minutes) as total
        FROM study_sessions
        WHERE user_id = ? AND date(start_time) = ? AND duration_minutes > 0
        GROUP BY subject
    ''', (_user_id(), today)).fetchall()
    conn.close()
    data = [{'subject': r['subject'], 'minutes': r['total']} for r in rows]
    return success_response({'data': data})


@analytics_bp.route('/focus-score', methods=['GET'])
@login_required
def focus_score():
    """Focus Score = (totalMinutes * streak) / (distractions + 1)."""
    conn = get_db()
    dates = get_session_dates(conn, _user_id(), days=30)
    streak_val = compute_streak(dates)
    row = conn.execute('''
        SELECT COALESCE(SUM(duration_minutes), 0) as total_minutes,
               COALESCE(SUM(distractions), 0) as total_distractions
        FROM study_sessions
        WHERE user_id = ? AND start_time >= date('now', '-30 days') AND duration_minutes > 0
    ''', (_user_id(),)).fetchone()
    conn.close()

    total = row['total_minutes'] or 0
    distractions = row['total_distractions'] or 0
    score = (total * streak_val) / (distractions + 1) if total else 0
    return success_response({
        'focus_score': round(score, 2),
        'total_minutes': total,
        'streak': streak_val,
        'distractions': distractions
    })


@analytics_bp.route('/heatmap', methods=['GET'])
@login_required
def heatmap():
    """Activity heatmap for last 12 weeks."""
    conn = get_db()
    rows = conn.execute('''
        SELECT date(start_time) as d, SUM(duration_minutes) as m
        FROM study_sessions
        WHERE user_id = ?
        GROUP BY date(start_time)
    ''', (_user_id(),)).fetchall()
    data_map = {r['d']: r['m'] for r in rows}
    conn.close()

    today = datetime.now(timezone.utc).date()
    result = []
    for i in range(84):
        day = today - timedelta(days=i)
        result.append({'date': day.isoformat(), 'minutes': data_map.get(day.isoformat(), 0)})
    return success_response({'data': result[::-1]})


@analytics_bp.route('/prediction', methods=['GET'])
@login_required
def prediction():
    """Predict tomorrow's study time from last 7 days average."""
    conn = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    row = conn.execute('''
        SELECT COALESCE(SUM(duration_minutes), 0) as total
        FROM study_sessions
        WHERE user_id = ? AND start_time >= ? AND duration_minutes > 0
    ''', (_user_id(), cutoff)).fetchone()
    conn.close()

    total = row['total'] or 0
    predicted = round(total / 7, 0) if total else 0
    return success_response({'predicted_minutes': int(predicted)})


@analytics_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Batched dashboard analytics - single request for all key metrics."""
    conn = get_db()
    uid = _user_id()
    today = datetime.now(timezone.utc).date()
    today_iso = today.isoformat()
    week_start = today - timedelta(days=today.weekday())

    daily_row = conn.execute('''
        SELECT COALESCE(SUM(duration_minutes), 0) as total
        FROM study_sessions
        WHERE user_id = ? AND date(start_time) = ? AND duration_minutes > 0
    ''', (uid, today_iso)).fetchone()

    weekly_rows = conn.execute('''
        SELECT subject, SUM(duration_minutes) as total
        FROM study_sessions
        WHERE user_id = ? AND date(start_time) >= ? AND duration_minutes > 0
        GROUP BY subject
    ''', (uid, week_start.isoformat())).fetchall()
    weekly_total = sum(r['total'] for r in weekly_rows)
    weekly_by_subject = {r['subject']: r['total'] for r in weekly_rows}

    dates = get_session_dates(conn, uid, days=365)
    streak_val = compute_streak(dates)

    days_out = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        row = conn.execute('''
            SELECT COALESCE(SUM(duration_minutes), 0) as total
            FROM study_sessions
            WHERE user_id = ? AND date(start_time) = ? AND duration_minutes > 0
        ''', (uid, d.isoformat())).fetchone()
        days_out.append({
            'day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i],
            'date': d.isoformat(),
            'minutes': row['total'],
            'is_today': d == today
        })

    subject_rows = conn.execute('''
        SELECT subject, SUM(duration_minutes) as total
        FROM study_sessions
        WHERE user_id = ? AND date(start_time) = ? AND duration_minutes > 0
        GROUP BY subject
    ''', (uid, today_iso)).fetchall()
    subject_data = [{'subject': r['subject'], 'minutes': r['total']} for r in subject_rows]

    focus_row = conn.execute('''
        SELECT COALESCE(SUM(duration_minutes), 0) as total_minutes,
               COALESCE(SUM(distractions), 0) as total_distractions
        FROM study_sessions
        WHERE user_id = ? AND start_time >= date('now', '-30 days') AND duration_minutes > 0
    ''', (uid,)).fetchone()
    total_minutes_30 = focus_row['total_minutes'] or 0
    distractions = focus_row['total_distractions'] or 0
    focus_score = (total_minutes_30 * streak_val) / (distractions + 1) if total_minutes_30 else 0

    heatmap_rows = conn.execute('''
        SELECT date(start_time) as d, SUM(duration_minutes) as m
        FROM study_sessions
        WHERE user_id = ?
        GROUP BY date(start_time)
    ''', (uid,)).fetchall()
    data_map = {r['d']: r['m'] for r in heatmap_rows}
    heatmap_data = []
    for i in range(84):
        day = today - timedelta(days=i)
        heatmap_data.append({'date': day.isoformat(), 'minutes': data_map.get(day.isoformat(), 0)})
    heatmap_data = heatmap_data[::-1]

    cutoff = (today - timedelta(days=7)).isoformat()
    pred_row = conn.execute('''
        SELECT COALESCE(SUM(duration_minutes), 0) as total
        FROM study_sessions
        WHERE user_id = ? AND start_time >= ? AND duration_minutes > 0
    ''', (uid, cutoff)).fetchone()
    pred_total = pred_row['total'] or 0
    predicted = int(round(pred_total / 7, 0)) if pred_total else 0

    session_rows = conn.execute('''
        SELECT subject, duration_minutes
        FROM study_sessions
        WHERE user_id = ? AND duration_minutes > 0
        ORDER BY created_at DESC
        LIMIT 5
    ''', (uid,)).fetchall()
    recent_sessions = [{'subject': r['subject'], 'minutes': r['duration_minutes']} for r in session_rows]

    conn.close()

    return success_response({
        'daily': {'total_minutes': daily_row['total'], 'date': today_iso},
        'weekly': {'total_minutes': weekly_total, 'by_subject': weekly_by_subject},
        'streak': streak_val,
        'weekly_progress': {'days': days_out},
        'subject_breakdown': {'data': subject_data},
        'focus_score': {'focus_score': round(focus_score, 2)},
        'heatmap': {'data': heatmap_data},
        'prediction': {'predicted_minutes': predicted},
        'recent_sessions': {'sessions': recent_sessions}
    })
