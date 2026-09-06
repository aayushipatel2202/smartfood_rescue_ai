from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import donors_collection, ngos_collection
from app.utils.auth_utils import hash_password, check_password, generate_token
from app.utils.geocode import forward_geocode

auth_bp = Blueprint("auth", __name__)


# ---------------- DONOR REGISTER ----------------
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

    result = donors_collection.insert_one(donor_doc)
    token = generate_token(str(result.inserted_id), "DONOR")

    return jsonify({
        "message": "Donor registered successfully",
        "token": token,
        "user": {
            "id": str(result.inserted_id),
            "organization_name": donor_doc["organization_name"],
            "email": donor_doc["email"],
            "role": "DONOR"
        }
    }), 201


# ---------------- DONOR LOGIN ----------------
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

    token = generate_token(str(donor["_id"]), "DONOR")

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(donor["_id"]),
            "organization_name": donor["organization_name"],
            "email": donor["email"],
            "role": "DONOR"
        }
    }), 200


# ---------------- NGO REGISTER ----------------
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

    result = ngos_collection.insert_one(ngo_doc)
    token = generate_token(str(result.inserted_id), "NGO")

    return jsonify({
        "message": "NGO registered successfully",
        "token": token,
        "user": {
            "id": str(result.inserted_id),
            "organization_name": ngo_doc["organization_name"],
            "email": ngo_doc["email"],
            "role": "NGO"
        }
    }), 201


# ---------------- NGO LOGIN ----------------
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

    token = generate_token(str(ngo["_id"]), "NGO")

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(ngo["_id"]),
            "organization_name": ngo["organization_name"],
            "email": ngo["email"],
            "role": "NGO"
        }
    }), 200