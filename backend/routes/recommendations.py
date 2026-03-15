"""Recommendations routes - weakest subject suggestion."""
from flask import Blueprint, session

from database.db import get_db
from utils.response import success_response, error_response

recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/api/recommendations')


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return error_response('Authentication required', 401)
        return f(*args, **kwargs)
    return decorated


@recommendations_bp.route('', methods=['GET'])
@login_required
def get_recommendations():
    """Suggest focus on weakest subject. Always filtered by user_id."""
    conn = get_db()
    rows = conn.execute('''
        SELECT subject, SUM(duration_minutes) as total
        FROM study_sessions
        WHERE user_id = ? AND start_time >= date('now', '-14 days') AND duration_minutes > 0
        GROUP BY subject
    ''', (session['user_id'],)).fetchall()

    all_subjects = [
        r['subject_name']
        for r in conn.execute(
            'SELECT subject_name FROM user_subjects WHERE user_id = ?',
            (session['user_id'],)
        ).fetchall()
    ]
    conn.close()

    by_subject = {r['subject']: r['total'] for r in rows}
    for s in all_subjects:
        if s not in by_subject:
            by_subject[s] = 0

    filtered = {k: v for k, v in by_subject.items() if k.lower() != 'other'}

    if not filtered:
        return success_response({
            'weakest_subject': None,
            'suggestion': 'Start your first session!',
            'by_subject': {}
        })

    weakest = min(filtered, key=filtered.get)
    suggestion = f'Focus on {weakest} today – your least studied subject.'
    return success_response({
        'weakest_subject': weakest,
        'suggestion': suggestion,
        'by_subject': filtered
    })
