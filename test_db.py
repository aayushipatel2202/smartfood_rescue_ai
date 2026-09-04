from app.extensions import db

print("Connected to:", db.name)
print("Collections:", db.list_collection_names())