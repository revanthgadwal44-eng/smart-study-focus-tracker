"""Study session routes."""
from datetime import datetime, timezone
import logging
from flask import Blueprint, request, session

from database.db import get_db
from utils.response import success_response, error_response
from utils.validation import validate_subject, sanitize_int

logger = logging.getLogger(__name__)

sessions_bp = Blueprint('sessions', __name__, url_prefix='/api/sessions')


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return error_response('Authentication required', 401)
        return f(*args, **kwargs)
    return decorated


@sessions_bp.route('', methods=['POST'])
@login_required
def create_session():
    """Create study session. Always scoped to user_id."""
    data = request.get_json() or {}

    subject = (data.get('subject') or '').strip()
    valid, err = validate_subject(subject)
    if not valid:
        return error_response(err, 400)

    seconds = sanitize_int(data.get('duration_seconds', 0), 0, 0)
    duration_minutes = max(0, round(seconds / 60))
    notes = (data.get('notes') or '').strip()[:2000]  # limit length
    distractions = sanitize_int(data.get('distractions', 0), 0, 0)

    start_time = datetime.now(timezone.utc).isoformat()
    end_time = start_time

    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO study_sessions
            (user_id, subject, start_time, end_time, duration_minutes, notes, distractions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            subject,
            start_time,
            end_time,
            duration_minutes,
            notes,
            distractions
        ))
        conn.commit()
        return success_response(None, 201)
    finally:
        conn.close()


@sessions_bp.route('', methods=['GET'])
@login_required
def list_sessions():
    """Get recent sessions. Always filtered by user_id."""
    limit = sanitize_int(request.args.get('limit', 5), 5, 1, 20)

    conn = get_db()
    try:
        rows = conn.execute('''
            SELECT subject, duration_minutes
            FROM study_sessions
            WHERE user_id = ? AND duration_minutes > 0
            ORDER BY created_at DESC
            LIMIT ?
        ''', (session['user_id'], limit)).fetchall()
        sessions = [{'subject': r['subject'], 'minutes': r['duration_minutes']} for r in rows]
        return success_response({'sessions': sessions})
    finally:
        conn.close()


@sessions_bp.route('/<int:sid>/distraction', methods=['POST'])
@login_required
def add_distraction(sid):
    """Increment distraction count. Only for user's sessions."""
    conn = get_db()
    row = conn.execute(
        'SELECT id, distractions FROM study_sessions WHERE id = ? AND user_id = ?',
        (sid, session['user_id'])
    ).fetchone()
    if not row:
        conn.close()
        return error_response('Session not found', 404)

    new_count = (row['distractions'] or 0) + 1
    conn.execute('UPDATE study_sessions SET distractions = ? WHERE id = ?', (new_count, sid))
    conn.commit()
    conn.close()
    return success_response({'distractions': new_count})
