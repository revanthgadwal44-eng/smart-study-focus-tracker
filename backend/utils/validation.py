"""Input validation utilities."""
import re

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{2,50}$')
SUBJECT_MAX_LEN = 100


def validate_email(email):
    """Validate email format. Returns (valid, error_message)."""
    if not email or not isinstance(email, str):
        return False, "Email required"
    email = email.strip().lower()
    if len(email) > 254:
        return False, "Invalid email"
    if not EMAIL_PATTERN.match(email):
        return False, "Invalid email format"
    return True, None


def validate_username(username):
    """Validate username. Returns (valid, error_message)."""
    if not username or not isinstance(username, str):
        return False, "Username required"
    username = username.strip()
    if len(username) < 2:
        return False, "Username too short"
    if len(username) > 50:
        return False, "Username too long"
    if not USERNAME_PATTERN.match(username):
        return False, "Username must contain only letters, numbers, underscore, hyphen"
    return True, None


def validate_password(password):
    """Validate password. Returns (valid, error_message)."""
    if not password or not isinstance(password, str):
        return False, "Password required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, None


def validate_subject(subject):
    """Validate subject name. Returns (valid, error_message)."""
    if not subject or not isinstance(subject, str):
        return False, "Subject name required"
    subject = subject.strip()
    if not subject:
        return False, "Subject name required"
    if len(subject) > SUBJECT_MAX_LEN:
        return False, f"Subject name too long (max {SUBJECT_MAX_LEN} chars)"
    return True, None


def sanitize_int(value, default=0, min_val=None, max_val=None):
    """Safely convert to int with optional bounds."""
    try:
        n = int(value) if value is not None else default
        if min_val is not None and n < min_val:
            return min_val
        if max_val is not None and n > max_val:
            return max_val
        return n
    except (ValueError, TypeError):
        return default
