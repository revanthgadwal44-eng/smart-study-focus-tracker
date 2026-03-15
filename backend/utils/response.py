"""Consistent API response helpers."""
from flask import jsonify


def success_response(data=None, status=200):
    """Return consistent success response: { success: true, data: ... }."""
    payload = {'success': True}
    if data is not None:
        payload['data'] = data
    return jsonify(payload), status


def error_response(message, status=400):
    """Return consistent error response: { success: false, error: ... }."""
    return jsonify({'success': False, 'error': message}), status
