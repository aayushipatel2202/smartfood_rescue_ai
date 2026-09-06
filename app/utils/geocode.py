import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def forward_geocode(address: str):
    """
    Converts a typed address into {lat, lng}.
    Returns None if geocoding fails (address should still be saved either way).
    """
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "SmartFoodRescueAI/1.0"},
            timeout=5
        )
        results = response.json()
        if results:
            return {
                "lat": float(results[0]["lat"]),
                "lng": float(results[0]["lon"])
            }
    except Exception as e:
        print("Geocoding failed:", e)
    return None