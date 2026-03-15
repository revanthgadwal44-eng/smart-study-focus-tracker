"""
Smart Study Focus Tracker - Backend API
Production-quality modular Flask REST API with SQLite
"""
import os
import logging

from flask import Flask, send_file

from database.db import init_db, get_db
from routes import (
    auth_bp, subjects_bp, sessions_bp, analytics_bp,
    gamification_bp, recommendations_bp, reports_bp, notifications_bp
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(subjects_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(gamification_bp)
app.register_blueprint(recommendations_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(notifications_bp)


# Initialize database
init_db()


@app.route('/')
def index():
    """Serve frontend."""
    return send_file(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html'))


@app.errorhandler(404)
def not_found(_e):
    from utils.response import error_response
    return error_response('Not found', 404)


@app.errorhandler(500)
def server_error(_e):
    from utils.response import error_response
    logger.exception("Server error")
    return error_response('Internal server error', 500)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
