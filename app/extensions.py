from pymongo import MongoClient
from app.config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

donors_collection = db["donors"]
ngos_collection = db["ngos"]
donations_collection = db["donations"]
ai_analysis_collection = db["ai_analysis"]
donation_acceptance_collection = db["donation_acceptance"]
donor_engagement_collection = db["donor_engagement"]
otp_codes_collection = db["otp_codes"]