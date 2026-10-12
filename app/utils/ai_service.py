import json
from google import genai
from app.config import Config

client = genai.Client(api_key=Config.GEMINI_API_KEY)

FALLBACK_ANALYSIS = {
    "estimated_meals": "Unavailable",
    "priority": "MEDIUM",
    "handling_recommendation": "Store appropriately and arrange pickup as soon as possible.",
    "summary": "AI analysis could not be generated for this donation.",
}


def generate_ai_analysis(donation: dict) -> dict:
    """
    Sends donation details to Gemini and returns a structured analysis dict.
    Falls back to a safe default if Gemini fails or returns bad data —
    a donation should NEVER fail to be created just because AI is unavailable.
    """
    prompt = f"""
You are a food safety and logistics assistant for a food donation platform that connects
food donors with NGOs for redistribution.

Analyze this food donation and respond:

Food name: {donation.get('food_name')}
Food type: {donation.get('food_type')}
Quantity: {donation.get('quantity')} {donation.get('unit')}
Description: {donation.get('description', 'None provided')}
Time posted: {donation.get('created_at')}
Expiry time: {donation.get('expiry_time')}

Respond ONLY with valid JSON in exactly this shape, no markdown formatting, no extra text:
{{
  "estimated_meals": <integer, your best estimate of how many meals this quantity provides>,
  "priority": "HIGH" or "MEDIUM" or "LOW" (based on how urgently this needs pickup given its expiry window),
  "handling_recommendation": "<one or two sentences on safe storage/handling>",
  "summary": "<one or two sentence plain-language summary of this donation for an NGO deciding whether to accept it>"
}}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        text = response.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()

        result = json.loads(text)

        # Basic validation — make sure Gemini gave us what we asked for
        required_keys = {"estimated_meals", "priority", "handling_recommendation", "summary"}
        if not required_keys.issubset(result.keys()):
            raise ValueError("Gemini response missing required fields")

        if result["priority"] not in ("HIGH", "MEDIUM", "LOW"):
            result["priority"] = "MEDIUM"

        return result

    except Exception as e:
        print("Gemini AI analysis failed:", e)
        return FALLBACK_ANALYSIS