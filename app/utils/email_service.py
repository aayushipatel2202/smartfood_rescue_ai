import random
import requests
from app.config import Config

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def send_otp_email(to_email: str, otp: str, purpose: str) -> bool:
    purpose_text = "complete your registration" if purpose == "REGISTER" else "log in"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 24px; border: 1px solid #eee; border-radius: 12px;">
      <h2 style="color: #1a2b4c;">SmartFood Rescue AI</h2>
      <p>Use the code below to {purpose_text}:</p>
      <div style="font-size: 32px; font-weight: bold; letter-spacing: 8px; background: #f5f5f0; padding: 16px; text-align: center; border-radius: 8px; color: #1a2b4c;">
        {otp}
      </div>
      <p style="color: #888; font-size: 12px; margin-top: 16px;">This code expires in 5 minutes. If you didn't request this, you can safely ignore this email.</p>
    </div>
    """

    payload = {
        "sender": {"name": Config.BREVO_SENDER_NAME, "email": Config.BREVO_SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": "Your SmartFood Rescue AI Verification Code",
        "htmlContent": html_body,
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": Config.BREVO_API_KEY,
    }

    try:
        response = requests.post(BREVO_URL, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            return True
        print("Brevo rejected the email:", response.status_code, response.text)
        return False
    except Exception as e:
        print("Failed to send OTP email:", e)
        return False