"""Route blueprints."""
from .auth import auth_bp
from .subjects import subjects_bp
from .sessions import sessions_bp
from .analytics import analytics_bp
from .gamification import gamification_bp
from .recommendations import recommendations_bp
from .reports import reports_bp
from .notifications import notifications_bp

__all__ = [
    'auth_bp',
    'subjects_bp',
    'sessions_bp',
    'analytics_bp',
    'gamification_bp',
    'recommendations_bp',
    'reports_bp',
    'notifications_bp',
]
