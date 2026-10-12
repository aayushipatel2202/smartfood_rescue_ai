from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from bson import ObjectId
from bson.errors import InvalidId

from app.extensions import donations_collection, donors_collection, ai_analysis_collection
from app.utils.decorators import token_required
from app.utils.serializers import serialize_donation, serialize_analysis
from app.utils.ai_service import generate_ai_analysis
from app.constants import STATUS_AVAILABLE 

from app.extensions import donation_acceptance_collection, donor_engagement_collection
from app.utils.serializers import serialize_acceptance
from app.constants import STATUS_ACCEPTED, STATUS_PICKED_UP, STATUS_COMPLETED, calculate_points

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

    analysis_result = generate_ai_analysis(donation_doc)
    analysis_doc = {
        "donation_id": result.inserted_id,
        "estimated_meals": analysis_result["estimated_meals"],
        "priority": analysis_result["priority"],
        "handling_recommendation": analysis_result["handling_recommendation"],
        "summary": analysis_result["summary"],
        "created_at": datetime.utcnow(),
    }
    ai_analysis_collection.insert_one(analysis_doc)

    return jsonify({
        "message": "Donation created successfully",
        "donation": serialize_donation(donation_doc),
        "analysis": serialize_analysis(analysis_doc)
    }), 201

@donation_bp.route("/<donation_id>/analysis", methods=["GET"])
@token_required()
def get_donation_analysis(donation_id):
    try:
        obj_id = ObjectId(donation_id)
    except InvalidId:
        return jsonify({"error": "Invalid donation id"}), 400

    analysis = ai_analysis_collection.find_one({"donation_id": obj_id})
    if not analysis:
        return jsonify({"error": "Analysis not available for this donation"}), 404

    return jsonify({"analysis": serialize_analysis(analysis)
    }), 200

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
        "expiry_time": {"$gt": datetime.utcnow()}   
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

@donation_bp.route("/<donation_id>/accept", methods=["POST"])
@token_required(role="NGO")
def accept_donation(donation_id):
    try:
        obj_id = ObjectId(donation_id)
    except InvalidId:
        return jsonify({"error": "Invalid donation id"}), 400

    donation = donations_collection.find_one({"_id": obj_id})
    if not donation:
        return jsonify({"error": "Donation not found"}), 404

    if donation["status"] != STATUS_AVAILABLE:
        return jsonify({"error": "This donation is no longer available"}), 409

    acceptance_doc = {
        "donation_id": obj_id,
        "ngo_id": ObjectId(request.user_id),
        "accepted_at": datetime.utcnow(),
        "pickup_status": STATUS_ACCEPTED,
        "completed_at": None,
    }
    donation_acceptance_collection.insert_one(acceptance_doc)
    donations_collection.update_one({"_id": obj_id}, {"$set": {"status": STATUS_ACCEPTED}})

    donation["status"] = STATUS_ACCEPTED
    return jsonify({
        "message": "Donation accepted successfully",
        "acceptance": serialize_acceptance(acceptance_doc, donation)
    }), 200

@donation_bp.route("/<donation_id>/pickup", methods=["PATCH"])
@token_required(role="NGO")
def mark_picked_up(donation_id):
    try:
        obj_id = ObjectId(donation_id)
    except InvalidId:
        return jsonify({"error": "Invalid donation id"}), 400

    acceptance = donation_acceptance_collection.find_one({
        "donation_id": obj_id,
        "ngo_id": ObjectId(request.user_id)
    })
    if not acceptance:
        return jsonify({"error": "You have not accepted this donation"}), 403

    donation = donations_collection.find_one({"_id": obj_id})
    if donation["status"] != STATUS_ACCEPTED:
        return jsonify({"error": f"Cannot mark as picked up from status {donation['status']}"}), 409

    donations_collection.update_one({"_id": obj_id}, {"$set": {"status": STATUS_PICKED_UP}})
    donation_acceptance_collection.update_one(
        {"_id": acceptance["_id"]},
        {"$set": {"pickup_status": STATUS_PICKED_UP}}
    )

    return jsonify({"message": "Marked as picked up"}), 200

@donation_bp.route("/<donation_id>/complete", methods=["PATCH"])
@token_required(role="NGO")
def mark_completed(donation_id):
    try:
        obj_id = ObjectId(donation_id)
    except InvalidId:
        return jsonify({"error": "Invalid donation id"}), 400

    acceptance = donation_acceptance_collection.find_one({
        "donation_id": obj_id,
        "ngo_id": ObjectId(request.user_id)
    })
    if not acceptance:
        return jsonify({"error": "You have not accepted this donation"}), 403

    donation = donations_collection.find_one({"_id": obj_id})
    if donation["status"] != STATUS_PICKED_UP:
        return jsonify({"error": f"Cannot complete from status {donation['status']}"}), 409

    # Update donation + acceptance status
    donations_collection.update_one({"_id": obj_id}, {"$set": {"status": STATUS_COMPLETED}})
    donation_acceptance_collection.update_one(
        {"_id": acceptance["_id"]},
        {"$set": {"pickup_status": STATUS_COMPLETED, "completed_at": datetime.utcnow()}}
    )

    analysis = ai_analysis_collection.find_one({"donation_id": obj_id})
    estimated_meals = analysis.get("estimated_meals") if analysis else None
    points_earned = calculate_points(estimated_meals)

    previous_total = donor_engagement_collection.find(
        {"donor_id": donation["donor_id"]}
    ).sort("created_at", -1).limit(1)
    previous_total = list(previous_total)
    running_total = (previous_total[0]["total_points"] if previous_total else 0) + points_earned

    from app.constants import get_donor_level
    new_level = get_donor_level(running_total)

    engagement_doc = {
        "donor_id": donation["donor_id"],
        "donation_id": obj_id,
        "points": points_earned,
        "total_points": running_total,
        "donor_level": new_level,
        "created_at": datetime.utcnow(),
    }
    donor_engagement_collection.insert_one(engagement_doc)

    return jsonify({
        "message": "Donation marked completed",
        "points_earned": points_earned,
        "total_points": running_total,
        "donor_level": new_level,
    }), 200

@donation_bp.route("/ngo/pickups", methods=["GET"])
@token_required(role="NGO")
def get_my_pickups():
    status_filter = request.args.get("status")  # ACCEPTED, PICKED_UP, or COMPLETED

    query = {"ngo_id": ObjectId(request.user_id)}
    if status_filter:
        query["pickup_status"] = status_filter.upper()

    acceptances = donation_acceptance_collection.find(query).sort("accepted_at", -1)

    results = []
    for acc in acceptances:
        donation = donations_collection.find_one({"_id": acc["donation_id"]})
        donor = donors_collection.find_one({"_id": donation["donor_id"]}) if donation else None
        acc_serialized = serialize_acceptance(acc, donation)
        if acc_serialized and donor:
            acc_serialized["donation"]["donor"] = {
                "id": str(donor["_id"]),
                "organization_name": donor.get("organization_name"),
                "phone": donor.get("phone"),
            }
        results.append(acc_serialized)

    return jsonify({"pickups": results}), 200