"""Subject management routes."""
import sqlite3
import logging
from flask import Blueprint, request, session

from database.db import get_db
from utils.response import success_response, error_response
from utils.validation import validate_subject

logger = logging.getLogger(__name__)

subjects_bp = Blueprint('subjects', __name__, url_prefix='/api/subjects')


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return error_response('Authentication required', 401)
        return f(*args, **kwargs)
    return decorated


@subjects_bp.route('', methods=['GET'])
@login_required
def get_subjects():
    """List user subjects. Always filtered by user_id."""
    conn = get_db()
    try:
        rows = conn.execute(
            'SELECT id, subject_name FROM user_subjects WHERE user_id = ? ORDER BY subject_name',
            (session['user_id'],)
        ).fetchall()
        subjects = [{'id': r['id'], 'name': r['subject_name']} for r in rows]
        return success_response({'subjects': subjects})
    finally:
        conn.close()


@subjects_bp.route('', methods=['POST'])
@login_required
def add_subject():
    """Add custom subject."""
    data = request.get_json() or {}
    subject = (data.get('subject') or '').strip()

    valid, err = validate_subject(subject)
    if not valid:
        return error_response(err, 400)

    conn = get_db()
    try:
        conn.execute(
            'INSERT INTO user_subjects (user_id, subject_name) VALUES (?, ?)',
            (session['user_id'], subject)
        )
        conn.commit()
        return success_response({'subject': subject}, 201)
    except sqlite3.IntegrityError:
        return error_response('Subject already exists', 409)
    finally:
        conn.close()


@subjects_bp.route('/<int:subject_id>', methods=['DELETE'])
@login_required
def delete_subject(subject_id):
    """Delete subject. Only for current user."""
    conn = get_db()
    cursor = conn.execute(
        'DELETE FROM user_subjects WHERE id = ? AND user_id = ?',
        (subject_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return error_response('Subject not found', 404)
    return success_response()


@subjects_bp.route('/<int:subject_id>', methods=['PUT'])
@login_required
def edit_subject(subject_id):
    """Edit subject name. Only for current user."""
    data = request.get_json() or {}
    new_name = (data.get('subject') or '').strip()

    valid, err = validate_subject(new_name)
    if not valid:
        return error_response(err, 400)

    conn = get_db()
    cursor = conn.execute(
        'UPDATE user_subjects SET subject_name = ? WHERE id = ? AND user_id = ?',
        (new_name, subject_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return error_response('Subject not found', 404)
    return success_response()
