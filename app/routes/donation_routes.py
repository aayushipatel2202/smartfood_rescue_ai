from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from bson import ObjectId
from bson.errors import InvalidId

from app.extensions import donations_collection, donors_collection
from app.utils.decorators import token_required
from app.utils.serializers import serialize_donation
from app.constants import STATUS_AVAILABLE

donation_bp = Blueprint("donation", __name__)

@donation_bp.route("", methods=["POST"])
@token_required(role="DONOR")
def create_donation():
    data = request.get_json()

    required_fields = ["food_name", "food_type", "quantity", "unit", "expiry_hours"]
    for field in required_fields:
        if data.get(field) in (None, ""):
            return jsonify({"error": f"{field} is required"}), 400

    try:
        quantity = float(data["quantity"])
        if quantity <= 0:
            return jsonify({"error": "quantity must be greater than 0"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "quantity must be a number"}), 400

    # Validate expiry window
    try:
        expiry_hours = float(data["expiry_hours"])
        if expiry_hours <= 0:
            return jsonify({"error": "expiry_hours must be greater than 0"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "expiry_hours must be a number"}), 400

    location = data.get("location")
    if not location or "lat" not in location or "lng" not in location:
        return jsonify({"error": "location with lat and lng is required"}), 400

    donation_doc = {
        "donor_id": ObjectId(request.user_id),
        "food_name": data["food_name"],
        "food_type": data["food_type"],
        "quantity": quantity,
        "unit": data["unit"],
        "description": data.get("description", ""),
        "pickup_location": data.get("pickup_location", ""),
        "location": {
            "lat": float(location["lat"]),
            "lng": float(location["lng"])
        },
        "image_url": data.get("image_url"),
        "status": STATUS_AVAILABLE,
        "created_at": datetime.utcnow(),
        "expiry_time": datetime.utcnow() + timedelta(hours=expiry_hours),
    }

    result = donations_collection.insert_one(donation_doc)
    donation_doc["_id"] = result.inserted_id

    return jsonify({
        "message": "Donation created successfully",
        "donation": serialize_donation(donation_doc)
    }), 201

@donation_bp.route("/mine", methods=["GET"])
@token_required(role="DONOR")
def get_my_donations():
    status_filter = request.args.get("status")

    query = {"donor_id": ObjectId(request.user_id)}
    if status_filter:
        query["status"] = status_filter.upper()

    donations = donations_collection.find(query).sort("created_at", -1)

    return jsonify({
        "donations": [serialize_donation(d) for d in donations]
    }), 200

@donation_bp.route("", methods=["GET"])
@token_required()
def get_available_donations():
    query = {
        "status": STATUS_AVAILABLE,
        "expiry_time": {"$gt": datetime.utcnow()}   # hide expired listings
    }

    food_type = request.args.get("food_type")
    if food_type:
        query["food_type"] = food_type

    donations = list(donations_collection.find(query).sort("created_at", -1))

    donor_ids = list({d["donor_id"] for d in donations})
    donors = {
        d["_id"]: d
        for d in donors_collection.find({"_id": {"$in": donor_ids}})
    }

    return jsonify({
        "donations": [
            serialize_donation(d, donors.get(d["donor_id"]))
            for d in donations
        ]
    }), 200

@donation_bp.route("/<donation_id>", methods=["GET"])
@token_required()
def get_donation(donation_id):
    try:
        obj_id = ObjectId(donation_id)
    except InvalidId:
        return jsonify({"error": "Invalid donation id"}), 400

    donation = donations_collection.find_one({"_id": obj_id})
    if not donation:
        return jsonify({"error": "Donation not found"}), 404

    donor = donors_collection.find_one({"_id": donation["donor_id"]})

    return jsonify({
        "donation": serialize_donation(donation, donor)
    }), 200

@donation_bp.route("/<donation_id>", methods=["DELETE"])
@token_required(role="DONOR")
def delete_donation(donation_id):
    try:
        obj_id = ObjectId(donation_id)
    except InvalidId:
        return jsonify({"error": "Invalid donation id"}), 400

    donation = donations_collection.find_one({"_id": obj_id})
    if not donation:
        return jsonify({"error": "Donation not found"}), 404

    if str(donation["donor_id"]) != request.user_id:
        return jsonify({"error": "You can only delete your own donations"}), 403

    if donation["status"] != STATUS_AVAILABLE:
        return jsonify({"error": "Cannot delete a donation that has already been accepted"}), 409

    donations_collection.delete_one({"_id": obj_id})
    return jsonify({"message": "Donation deleted successfully"}), 200