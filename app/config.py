import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    #SMTP_EMAIL = os.getenv("SMTP_EMAIL")
    #SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    #SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    #SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
    BREVO_API_KEY = os.getenv("BREVO_API_KEY")
    BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")
    BREVO_SENDER_NAME = os.getenv("BREVO_SENDER_NAME", "SmartFood Rescue AI")