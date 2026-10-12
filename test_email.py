import requests
from dotenv import load_dotenv
import os

load_dotenv()

payload = {
    "sender": {"name": os.getenv("BREVO_SENDER_NAME"), "email": os.getenv("BREVO_SENDER_EMAIL")},
    "to": [{"email": os.getenv("BREVO_SENDER_EMAIL")}],  # sending to yourself
    "subject": "Brevo test",
    "htmlContent": "<p>If you can read this, Brevo works.</p>",
}
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "api-key": os.getenv("BREVO_API_KEY"),
}

r = requests.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers, timeout=10)
print(r.status_code, r.text)