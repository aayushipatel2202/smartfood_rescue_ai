from app.extensions import donations_collection, donors_collection, ngos_collection

donors_collection.create_index("email", unique=True)
ngos_collection.create_index("email", unique=True)
donations_collection.create_index([("status", 1), ("expiry_time", -1)])
donations_collection.create_index([("donor_id", 1), ("created_at", -1)])

print("Indexes created successfully")

from app.extensions import otp_codes_collection
otp_codes_collection.create_index("expires_at", expireAfterSeconds=0)