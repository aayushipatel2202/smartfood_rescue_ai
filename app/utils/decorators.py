from functools import wraps
from flask import request, jsonify
from app.utils.auth_utils import decode_token

def token_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid Authorization header"}), 401

            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401

            if role and payload["role"] != role:
                return jsonify({"error": f"Access restricted to {role} accounts"}), 403

            request.user_id = payload["user_id"]
            request.user_role = payload["role"]
            return f(*args, **kwargs)
        return wrapper
    return decorator