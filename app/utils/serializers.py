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