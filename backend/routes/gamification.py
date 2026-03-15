"""Gamification routes - XP, level, badges."""
from flask import Blueprint, session

from database.db import get_db
from services.analytics import get_session_dates, compute_streak
from utils.response import success_response, error_response

gamification_bp = Blueprint('gamification', __name__, url_prefix='/api/gamification')


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return error_response('Authentication required', 401)
        return f(*args, **kwargs)
    return decorated


@gamification_bp.route('', methods=['GET'])
@login_required
def get_gamification():
    """XP, level, badges. Always filtered by user_id."""
    conn = get_db()
    row = conn.execute('''
        SELECT COALESCE(SUM(duration_minutes), 0) as total
        FROM study_sessions WHERE user_id = ? AND duration_minutes > 0
    ''', (session['user_id'],)).fetchone()
    total_minutes = row['total']

    dates = get_session_dates(conn, session['user_id'], days=365)
    streak = compute_streak(dates)
    conn.close()

    xp = total_minutes
    level = max(1, (xp // 500) + 1)
    xp_in_level = xp % 500
    xp_for_next = 500

    badges = []
    if streak >= 30:
        badges.append({'id': 'gold', 'name': 'Gold', 'days': 30})
    if streak >= 7:
        badges.append({'id': 'silver', 'name': 'Silver', 'days': 7})
    if streak >= 3:
        badges.append({'id': 'bronze', 'name': 'Bronze', 'days': 3})

    return success_response({
        'xp': xp,
        'level': level,
        'xp_in_level': xp_in_level,
        'xp_for_next': xp_for_next,
        'badges': badges,
        'streak': streak
    })
