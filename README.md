# SmartFood Rescue AI Backend

Flask REST API for a food-rescue platform that connects food donors with NGOs. Donors can post food donations, NGOs can claim and track pickups, and the API provides donation statistics and AI-generated donation guidance.

## Features

- Donor and NGO registration and login with email OTP verification
- JWT bearer-token authentication and role-based access control
- Donation creation, browsing, acceptance, pickup, and completion tracking
- Donation impact and dashboard statistics
- Gemini-powered meal estimates, priority, and food-handling recommendations
- MongoDB persistence
- Address geocoding through OpenStreetMap Nominatim

## Technology

- Python and Flask
- MongoDB with PyMongo
- JWT and bcrypt for authentication
- Google Gemini API for donation analysis
- Brevo for OTP email delivery

## Frontend

A separate frontend for this project is developed by my friend. It is available in the [SmartFood Rescue AI frontend repository](https://github.com/pateljulsi-oss/-smartfood-rescue-ai).

## Prerequisites

- Python and pip
- A MongoDB instance and database
- API credentials for Google Gemini and Brevo

## Setup

1. Clone the repository and enter the project directory:

   ```bash
   git clone https://github.com/aayushipatel2202/smartfood_rescue_ai.git
   cd smartfood_rescue_ai
   ```

2. Create and activate a virtual environment:

   **Windows PowerShell**

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and set the following values:

   ```dotenv
   MONGO_URI=mongodb://localhost:27017/
   DB_NAME=smartfood_rescue
   JWT_SECRET_KEY=replace_with_a_long_random_secret
   GEMINI_API_KEY=your_gemini_api_key
   BREVO_API_KEY=your_brevo_api_key
   BREVO_SENDER_EMAIL=verified_sender@example.com
   BREVO_SENDER_NAME=SmartFood Rescue AI
   ```

   Use your actual MongoDB connection string and service credentials. Keep `.env` private; it is excluded from Git.

5. Create the MongoDB indexes:

   ```bash
   python create_indexes.py
   ```

## Run the API

```bash
python run.py
```

The development server runs at `http://127.0.0.1:5000`. The app enables CORS and exposes a health check:

```http
GET /api/health
```

## API Endpoints

Unless noted otherwise, protected endpoints require:

```http
Authorization: Bearer <token>
```

### Authentication

Registration and login send an OTP to the supplied email. Call `/verify-otp` with the email, OTP, role (`DONOR` or `NGO`), and purpose (`REGISTER` or `LOGIN`) to complete the operation and receive a token.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/donor/register` | Start donor registration |
| `POST` | `/api/auth/donor/login` | Start donor login |
| `POST` | `/api/auth/ngo/register` | Start NGO registration |
| `POST` | `/api/auth/ngo/login` | Start NGO login |
| `POST` | `/api/auth/verify-otp` | Verify registration or login OTP |
| `POST` | `/api/auth/resend-otp` | Request another OTP |

### Donations

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `POST` | `/api/donations` | Donor | Create a donation and generate its AI analysis |
| `GET` | `/api/donations` | Authenticated | List currently available donations; optional `food_type` query parameter |
| `GET` | `/api/donations/mine` | Donor | List the donor's donations; optional `status` query parameter |
| `GET` | `/api/donations/<donation_id>` | Authenticated | Get a donation |
| `GET` | `/api/donations/<donation_id>/analysis` | Authenticated | Get its AI analysis |
| `DELETE` | `/api/donations/<donation_id>` | Donor | Delete an available donation owned by the donor |
| `POST` | `/api/donations/<donation_id>/accept` | NGO | Accept an available donation |
| `PATCH` | `/api/donations/<donation_id>/pickup` | NGO | Mark an accepted donation as picked up |
| `PATCH` | `/api/donations/<donation_id>/complete` | NGO | Mark a pickup as completed |
| `GET` | `/api/donations/ngo/pickups` | NGO | List the NGO's pickups |

### Dashboard

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/api/donor/stats` | Donor | Get donor donation and impact statistics |
| `GET` | `/api/ngo/stats` | NGO | Get NGO pickup and meal statistics |

## Donation request example

`POST /api/donations` requires a donor token and a JSON body containing food details, expiry duration, and latitude/longitude for the pickup location:

```json
{
  "food_name": "Fresh produce",
  "food_type": "Vegetables",
  "quantity": 10,
  "unit": "kg",
  "expiry_hours": 24,
  "location": {
    "lat": 37.7749,
    "lng": -122.4194
  },
  "pickup_location": "Main entrance",
  "description": "Freshly packed produce"
}
```

The response includes the created donation and an AI analysis. An `image_url` may also be provided.

## Project layout

```text
smartfood_rescue_ai/
├── app/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── ai_routes.py
│   │   ├── auth_routes.py
│   │   ├── dashboard_routes.py
│   │   ├── donation_routes.py
│   │   └── ngo_routes.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── ai_service.py
│   │   ├── auth_utils.py
│   │   ├── decorators.py
│   │   ├── email_service.py
│   │   ├── geocode.py
│   │   └── serializers.py
│   ├── __init__.py
│   ├── config.py
│   ├── constants.py
│   └── extensions.py
├── .gitignore
├── create_indexes.py
├── README.md
├── requirements.txt
├── run.py
├── test_db.py
└── test_email.py
```

`test_db.py` and `test_email.py` are standalone connection/email check scripts; they are not an automated test suite.
