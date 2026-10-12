from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime

from app.extensions import (
    donations_collection, ai_analysis_collection,
    donor_engagement_collection, donation_acceptance_collection
)
from app.utils.decorators import token_required
from app.constants import STATUS_AVAILABLE, STATUS_COMPLETED

dashboard_bp = Blueprint("dashboard", __name__)


def _sum_meals_for_donation_ids(donation_ids):
    total = 0
    for analysis in ai_analysis_collection.find({"donation_id": {"$in": donation_ids}}):
        try:
            total += int(float(analysis.get("estimated_meals")))
        except (TypeError, ValueError):
            continue
    return total


@dashboard_bp.route("/donor/stats", methods=["GET"])
@token_required(role="DONOR")
def donor_stats():
    donor_id = ObjectId(request.user_id)

    total_donations = donations_collection.count_documents({"donor_id": donor_id})
    completed_rescues = donations_collection.count_documents({"donor_id": donor_id, "status": STATUS_COMPLETED})

    my_donation_ids = [d["_id"] for d in donations_collection.find({"donor_id": donor_id}, {"_id": 1})]
    estimated_meals = _sum_meals_for_donation_ids(my_donation_ids)

    latest_engagement = list(
        donor_engagement_collection.find({"donor_id": donor_id}).sort("created_at", -1).limit(1)
    )
    total_points = latest_engagement[0]["total_points"] if latest_engagement else 0
    donor_level = latest_engagement[0]["donor_level"] if latest_engagement else "BRONZE"

    return jsonify({
        "totalDonations": total_donations,
        "completedRescues": completed_rescues,
        "estimatedMeals": estimated_meals,
        "impactPoints": total_points,
        "level": donor_level,
    }), 200


@dashboard_bp.route("/ngo/stats", methods=["GET"])
@token_required(role="NGO")
def ngo_stats():
    ngo_id = ObjectId(request.user_id)

    available_now = donations_collection.count_documents({
        "status": STATUS_AVAILABLE,
        "expiry_time": {"$gt": datetime.utcnow()}
    })
    my_claims = donation_acceptance_collection.count_documents({
        "ngo_id": ngo_id,
        "pickup_status": {"$in": ["ACCEPTED", "PICKED_UP"]}
    })
    completed_pickups = donation_acceptance_collection.count_documents({
        "ngo_id": ngo_id,
        "pickup_status": STATUS_COMPLETED
    })

    completed_donation_ids = [
        a["donation_id"] for a in donation_acceptance_collection.find(
            {"ngo_id": ngo_id, "pickup_status": STATUS_COMPLETED}, {"donation_id": 1}
        )
    ]
    meals_distributed = _sum_meals_for_donation_ids(completed_donation_ids)

    return jsonify({
        "availableToday": available_now,
        "acceptedRescues": my_claims,
        "completedPickups": completed_pickups,
        "mealsDistributed": meals_distributed,
    }), 200