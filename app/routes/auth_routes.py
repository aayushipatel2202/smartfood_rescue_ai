from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from app.extensions import donors_collection, ngos_collection, otp_codes_collection
from app.utils.auth_utils import hash_password, check_password, generate_token
from app.utils.geocode import forward_geocode
from app.utils.email_service import generate_otp, send_otp_email

auth_bp = Blueprint("auth", __name__)

OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


def _create_and_send_otp(email, role, purpose, pending_payload=None):
    otp_code = generate_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp_codes_collection.delete_many({"email": email, "role": role, "purpose": purpose})

    otp_codes_collection.insert_one({
        "email": email,
        "role": role,
        "purpose": purpose,
        "otp_code": otp_code,
        "expires_at": expires_at,
        "attempts": 0,
        "pending_payload": pending_payload,
        "created_at": datetime.utcnow(),
    })

    email_sent = send_otp_email(email, otp_code, purpose)
    return email_sent


# ---------------- DONOR REGISTER (Step 1: sends OTP, does NOT create account yet) ----------------
@auth_bp.route("/donor/register", methods=["POST"])
def donor_register():
    data = request.get_json()

    required_fields = ["organization_name", "contact_person", "email", "phone", "address", "password"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if donors_collection.find_one({"email": data["email"]}):
        return jsonify({"error": "Email already registered"}), 409

    location = forward_geocode(data["address"])

    donor_doc = {
        "organization_name": data["organization_name"],
        "contact_person": data["contact_person"],
        "email": data["email"],
        "password_hash": hash_password(data["password"]),
        "phone": data["phone"],
        "address": data["address"],
        "location": location,
        "created_at": datetime.utcnow()
    }

    email_sent = _create_and_send_otp(data["email"], "DONOR", "REGISTER", pending_payload=donor_doc)

    if not email_sent:
        return jsonify({"error": "Failed to send verification email. Please try again in a moment."}), 502

    return jsonify({
        "message": "OTP sent to your email. Please verify to complete registration.",
        "email": data["email"]
    }), 202


# ---------------- DONOR LOGIN (Step 1: validates password, sends OTP, does NOT issue token yet) ----------------
@auth_bp.route("/donor/login", methods=["POST"])
def donor_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    donor = donors_collection.find_one({"email": email})
    if not donor or not check_password(password, donor["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    email_sent = _create_and_send_otp(email, "DONOR", "LOGIN")

    if not email_sent:
        return jsonify({"error": "Failed to send verification email. Please try again in a moment."}), 502

    return jsonify({
        "message": "OTP sent to your email. Please verify to log in.",
        "email": email
    }), 202


# ---------------- NGO REGISTER (Step 1) ----------------
@auth_bp.route("/ngo/register", methods=["POST"])
def ngo_register():
    data = request.get_json()

    required_fields = ["organization_name", "contact_person", "email", "phone", "address", "password"]
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    if ngos_collection.find_one({"email": data["email"]}):
        return jsonify({"error": "Email already registered"}), 409

    location = forward_geocode(data["address"])

    ngo_doc = {
        "organization_name": data["organization_name"],
        "contact_person": data["contact_person"],
        "email": data["email"],
        "password_hash": hash_password(data["password"]),
        "phone": data["phone"],
        "address": data["address"],
        "service_description": data.get("service_description", ""),
        "location": location,
        "created_at": datetime.utcnow()
    }

    email_sent = _create_and_send_otp(data["email"], "NGO", "REGISTER", pending_payload=ngo_doc)

    if not email_sent:
        return jsonify({"error": "Failed to send verification email. Please try again in a moment."}), 502

    return jsonify({
        "message": "OTP sent to your email. Please verify to complete registration.",
        "email": data["email"]
    }), 202


# ---------------- NGO LOGIN (Step 1) ----------------
@auth_bp.route("/ngo/login", methods=["POST"])
def ngo_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    ngo = ngos_collection.find_one({"email": email})
    if not ngo or not check_password(password, ngo["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    email_sent = _create_and_send_otp(email, "NGO", "LOGIN")

    if not email_sent:
        return jsonify({"error": "Failed to send verification email. Please try again in a moment."}), 502

    return jsonify({
        "message": "OTP sent to your email. Please verify to log in.",
        "email": email
    }), 202


# ---------------- VERIFY OTP (Step 2: shared by register + login, both roles) ----------------
@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    otp = data.get("otp")
    role = (data.get("role") or "").upper()
    purpose = (data.get("purpose") or "").upper()

    if not email or not otp or role not in ("DONOR", "NGO") or purpose not in ("REGISTER", "LOGIN"):
        return jsonify({"error": "email, otp, role, and purpose are required"}), 400

    record = otp_codes_collection.find_one({"email": email, "role": role, "purpose": purpose})
    if not record:
        return jsonify({"error": "No pending verification found. Please try registering or logging in again."}), 404

    if record["expires_at"] < datetime.utcnow():
        otp_codes_collection.delete_one({"_id": record["_id"]})
        return jsonify({"error": "OTP has expired. Please request a new one."}), 410

    if record["otp_code"] != otp:
        new_attempts = record["attempts"] + 1
        if new_attempts >= MAX_OTP_ATTEMPTS:
            otp_codes_collection.delete_one({"_id": record["_id"]})
            return jsonify({"error": "Too many incorrect attempts. Please request a new OTP."}), 429
        otp_codes_collection.update_one({"_id": record["_id"]}, {"$set": {"attempts": new_attempts}})
        return jsonify({"error": f"Incorrect OTP. {MAX_OTP_ATTEMPTS - new_attempts} attempt(s) remaining."}), 400

    collection = donors_collection if role == "DONOR" else ngos_collection

    if purpose == "REGISTER":
        account_doc = record["pending_payload"]
        result = collection.insert_one(account_doc)
        account_id = result.inserted_id
        account_doc["_id"] = account_id
    else:  # LOGIN
        account_doc = collection.find_one({"email": email})
        if not account_doc:
            otp_codes_collection.delete_one({"_id": record["_id"]})
            return jsonify({"error": "Account not found"}), 404
        account_id = account_doc["_id"]

    otp_codes_collection.delete_one({"_id": record["_id"]})
    token = generate_token(str(account_id), role)

    user_response = {
        "id": str(account_id),
        "organization_name": account_doc["organization_name"],
        "contact_person": account_doc.get("contact_person", ""),
        "email": account_doc["email"],
        "phone": account_doc.get("phone", ""),
        "address": account_doc.get("address", ""),
        "role": role,
    }
    if role == "NGO":
        user_response["service_description"] = account_doc.get("service_description", "")

    status_code = 201 if purpose == "REGISTER" else 200
    return jsonify({
        "message": "Verified successfully",
        "token": token,
        "user": user_response
    }), status_code


# ---------------- RESEND OTP ----------------
@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    data = request.get_json()
    email = data.get("email")
    role = (data.get("role") or "").upper()
    purpose = (data.get("purpose") or "").upper()

    if not email or role not in ("DONOR", "NGO") or purpose not in ("REGISTER", "LOGIN"):
        return jsonify({"error": "email, role, and purpose are required"}), 400

    record = otp_codes_collection.find_one({"email": email, "role": role, "purpose": purpose})
    if not record:
        return jsonify({"error": "No pending verification found. Please try registering or logging in again."}), 404

    email_sent = _create_and_send_otp(email, role, purpose, pending_payload=record.get("pending_payload"))

    if not email_sent:
        return jsonify({"error": "Failed to send verification email. Please try again in a moment."}), 502

    return jsonify({"message": "A new OTP has been sent to your email."}), 200