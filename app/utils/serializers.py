def serialize_donation(donation, donor=None):
    """Converts a MongoDB donation document into a JSON-safe dict."""
    if not donation:
        return None

    result = {
        "id": str(donation["_id"]),
        "food_name": donation.get("food_name"),
        "food_type": donation.get("food_type"),
        "quantity": donation.get("quantity"),
        "unit": donation.get("unit"),
        "description": donation.get("description", ""),
        "pickup_location": donation.get("pickup_location", ""),
        "location": donation.get("location"),
        "image_url": donation.get("image_url"),
        "status": donation.get("status"),
        "created_at": donation["created_at"].isoformat() if donation.get("created_at") else None,
        "expiry_time": donation["expiry_time"].isoformat() if donation.get("expiry_time") else None,
    }

    if donor:
        result["donor"] = {
            "id": str(donor["_id"]),
            "organization_name": donor.get("organization_name"),
            "phone": donor.get("phone"),
            "address": donor.get("address"),
        }

    return result

def serialize_analysis(analysis):
    if not analysis:
        return None
    return {
        "id": str(analysis["_id"]),
        "donation_id": str(analysis["donation_id"]),
        "estimated_meals": analysis.get("estimated_meals"),
        "priority": analysis.get("priority"),
        "handling_recommendation": analysis.get("handling_recommendation"),
        "summary": analysis.get("summary"),
        "created_at": analysis["created_at"].isoformat() if analysis.get("created_at") else None,
    }

def serialize_acceptance(acceptance, donation=None):
    if not acceptance:
        return None
    result = {
        "id": str(acceptance["_id"]),
        "donation_id": str(acceptance["donation_id"]),
        "ngo_id": str(acceptance["ngo_id"]),
        "accepted_at": acceptance["accepted_at"].isoformat() if acceptance.get("accepted_at") else None,
        "pickup_status": acceptance.get("pickup_status"),
        "completed_at": acceptance["completed_at"].isoformat() if acceptance.get("completed_at") else None,
    }
    if donation:
        result["donation"] = serialize_donation(donation)
    return result