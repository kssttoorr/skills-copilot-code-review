"""
MongoDB database configuration and setup for Mergington High School API
"""

from pymongo import MongoClient
from argon2 import PasswordHasher, exceptions as argon2_exceptions
from datetime import datetime, timezone
from bson.objectid import ObjectId

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['mergington_high']
activities_collection = db['activities']
teachers_collection = db['teachers']
announcements_collection = db['announcements']

# Methods


def hash_password(password):
    """Hash password using Argon2"""
    ph = PasswordHasher()
    return ph.hash(password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    """Verify a plain password against an Argon2 hashed password.

    Returns True when the password matches, False otherwise.
    """
    ph = PasswordHasher()
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except argon2_exceptions.VerifyMismatchError:
        return False
    except Exception:
        # For any other exception (e.g., invalid hash), treat as non-match
        return False


def init_database():
    """Initialize database if empty"""

    # Initialize activities if empty
    if activities_collection.count_documents({}) == 0:
        for name, details in initial_activities.items():
            activities_collection.insert_one({"_id": name, **details})

    # Initialize teacher accounts if empty
    if teachers_collection.count_documents({}) == 0:
        for teacher in initial_teachers:
            teachers_collection.insert_one(
                {"_id": teacher["username"], **teacher})

    # Initialize announcements with an example if empty
    if announcements_collection.count_documents({}) == 0:
        # Example announcement: registration open until end of current month
        now = datetime.now(timezone.utc)
        end_of_month = datetime(now.year, now.month, 28, 23, 59, 59, tzinfo=timezone.utc)
        # If month has more than 28 days, set a safe future expiration (approx end of month)
        announcements_collection.insert_one({
            "title": "Activity registration open",
            "message": "Activity registration is open until the end of the month. Don't miss your spot!",
            "start": None,
            "expires": end_of_month,
            "created_at": now
        })


def get_active_announcements(now: datetime = None):
    """Return announcements where now is between start (if provided) and expires."""
    if now is None:
        now = datetime.now(timezone.utc)

    # Query: expires > now and (start is None or start <= now)
    query = {
        "expires": {"$gt": now},
        "$or": [
            {"start": None},
            {"start": {"$lte": now}}
        ]
    }
    docs = announcements_collection.find(query).sort("created_at", -1)
    result = []
    for d in docs:
        result.append({
            "id": str(d.get("_id")),
            "title": d.get("title"),
            "message": d.get("message"),
            "start": d.get("start"),
            "expires": d.get("expires"),
            "created_at": d.get("created_at")
        })
    return result


def list_announcements(include_expired: bool = False):
    """List announcements; by default excludes expired ones."""
    now = datetime.now(timezone.utc)
    if include_expired:
        docs = announcements_collection.find().sort("created_at", -1)
    else:
        docs = announcements_collection.find({"expires": {"$gt": now}}).sort("created_at", -1)

    result = []
    for d in docs:
        result.append({
            "id": str(d.get("_id")),
            "title": d.get("title"),
            "message": d.get("message"),
            "start": d.get("start"),
            "expires": d.get("expires"),
            "created_at": d.get("created_at")
        })
    return result


def create_announcement(title: str, message: str, expires: datetime, start: datetime = None):
    now = datetime.now(timezone.utc)
    doc = {
        "title": title,
        "message": message,
        "start": start,
        "expires": expires,
        "created_at": now
    }
    res = announcements_collection.insert_one(doc)
    return str(res.inserted_id)


def update_announcement(ann_id: str, fields: dict):
    # Accepts datetime objects for start/expires if present
    _id = ObjectId(ann_id)
    announcements_collection.update_one({"_id": _id}, {"$set": fields})
    return ann_id


def delete_announcement(ann_id: str):
    _id = ObjectId(ann_id)
    announcements_collection.delete_one({"_id": _id})
    return ann_id

# Initial database if empty
initial_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Mondays and Fridays, 3:15 PM - 4:45 PM",
        "schedule_details": {
            "days": ["Monday", "Friday"],
            "start_time": "15:15",
            "end_time": "16:45"
        },
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 7:00 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "07:00",
            "end_time": "08:00"
        },
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Morning Fitness": {
        "description": "Early morning physical training and exercises",
        "schedule": "Mondays, Wednesdays, Fridays, 6:30 AM - 7:45 AM",
        "schedule_details": {
            "days": ["Monday", "Wednesday", "Friday"],
            "start_time": "06:30",
            "end_time": "07:45"
        },
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and compete in basketball tournaments",
        "schedule": "Wednesdays and Fridays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Wednesday", "Friday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore various art techniques and create masterpieces",
        "schedule": "Thursdays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Thursday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Monday", "Wednesday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and prepare for math competitions",
        "schedule": "Tuesdays, 7:15 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday"],
            "start_time": "07:15",
            "end_time": "08:00"
        },
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Friday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "amelia@mergington.edu"]
    },
    "Weekend Robotics Workshop": {
        "description": "Build and program robots in our state-of-the-art workshop",
        "schedule": "Saturdays, 10:00 AM - 2:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "10:00",
            "end_time": "14:00"
        },
        "max_participants": 15,
        "participants": ["ethan@mergington.edu", "oliver@mergington.edu"]
    },
    "Science Olympiad": {
        "description": "Weekend science competition preparation for regional and state events",
        "schedule": "Saturdays, 1:00 PM - 4:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "13:00",
            "end_time": "16:00"
        },
        "max_participants": 18,
        "participants": ["isabella@mergington.edu", "lucas@mergington.edu"]
    },
    "Sunday Chess Tournament": {
        "description": "Weekly tournament for serious chess players with rankings",
        "schedule": "Sundays, 2:00 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Sunday"],
            "start_time": "14:00",
            "end_time": "17:00"
        },
        "max_participants": 16,
        "participants": ["william@mergington.edu", "jacob@mergington.edu"]
    }
}

initial_teachers = [
    {
        "username": "mrodriguez",
        "display_name": "Ms. Rodriguez",
        "password": hash_password("art123"),
        "role": "teacher"
    },
    {
        "username": "mchen",
        "display_name": "Mr. Chen",
        "password": hash_password("chess456"),
        "role": "teacher"
    },
    {
        "username": "principal",
        "display_name": "Principal Martinez",
        "password": hash_password("admin789"),
        "role": "admin"
    }
]
