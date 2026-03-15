"""Notification check route."""
from datetime import datetime, timezone
from flask import Blueprint, session

from database.db import get_db
from utils.response import success_response, error_response

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return error_response('Authentication required', 401)
        return f(*args, **kwargs)
    return decorated


@notifications_bp.route('/check', methods=['GET'])
@login_required
def check():
    """Check if user has studied today."""
    conn = get_db()
    today = datetime.now(timezone.utc).date().isoformat()
    row = conn.execute('''
        SELECT 1 FROM study_sessions
        WHERE user_id = ? AND date(start_time) = ? AND duration_minutes > 0
        LIMIT 1
    ''', (session['user_id'], today)).fetchone()
    conn.close()
    studied_today = row is not None
    return success_response({
        'studied_today': studied_today,
        'should_remind': not studied_today
    })
