"""Analytics business logic - shared by routes."""
from datetime import datetime, timedelta, timezone


def get_session_dates(conn, user_id, days=7):
    """Get distinct dates with sessions for streak/analytics."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = conn.execute('''
        SELECT DISTINCT date(start_time) as d
        FROM study_sessions
        WHERE user_id = ? AND start_time >= ? AND duration_minutes > 0
        ORDER BY d DESC
    ''', (user_id, cutoff)).fetchall()
    return [r['d'] for r in rows]


def compute_streak(dates):
    """Compute consecutive day streak from today backward."""
    if not dates:
        return 0
    today = datetime.now(timezone.utc).date().isoformat()
    if today not in dates:
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        if yesterday not in dates:
            return 0
        target = yesterday
    else:
        target = today

    streak = 0
    current = datetime.fromisoformat(target).date()
    check_dates = set(dates)

    while current.isoformat() in check_dates:
        streak += 1
        current -= timedelta(days=1)

    return streak
