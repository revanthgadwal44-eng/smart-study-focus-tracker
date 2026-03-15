"""Authentication routes."""
import sqlite3
import logging
from flask import Blueprint, request, session
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db
from utils.response import success_response, error_response
from utils.validation import validate_email, validate_username, validate_password

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def login_required(f):
    """Decorator for routes requiring authentication."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return error_response('Authentication required', 401)
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Register new user."""
    data = request.get_json()
    if not data:
        return error_response('Missing data', 400)

    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')

    valid, err = validate_username(username)
    if not valid:
        return error_response(err, 400)
    valid, err = validate_email(email)
    if not valid:
        return error_response(err, 400)
    valid, err = validate_password(password)
    if not valid:
        return error_response(err, 400)

    conn = get_db()
    try:
        password_hash = generate_password_hash(password)
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        user_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return error_response('User already exists', 409)
    except Exception as e:
        conn.close()
        logger.exception("Signup failed")
        return error_response('Registration failed', 500)
    conn.close()

    session['user_id'] = user_id
    session['username'] = username
    return success_response({'user': {'id': user_id, 'username': username}}, 201)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user."""
    data = request.get_json()
    if not data:
        return error_response('Email and password required', 400)

    email = (data.get('email') or '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return error_response('Email and password required', 400)

    conn = get_db()
    user = conn.execute(
        'SELECT id, username, password_hash FROM users WHERE email = ?',
        (email,)
    ).fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return error_response('Invalid email or password', 401)

    session['user_id'] = user['id']
    session['username'] = user['username']
    return success_response({'user': {'id': user['id'], 'username': user['username']}})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """End session."""
    session.clear()
    return success_response()


@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    """Get current user."""
    return success_response({
        'user': {'id': session['user_id'], 'username': session['username']}
    })
