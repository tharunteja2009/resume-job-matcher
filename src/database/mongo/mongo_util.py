# importing module
from pymongo import MongoClient, errors
from autogen_core.tools import FunctionTool
from config.settings import get_config
import json
import hashlib
import os


def get_mongo_uri():
    """Get MongoDB connection URI from configuration."""
    config = get_config()
    return config.database.uri


def get_mongo_client():
    """Get MongoDB client and database connection."""
    config = get_config()
    client = MongoClient(get_mongo_uri())
    # Access database
    mydatabase = client[config.database.database]
    return mydatabase


def get_collection_names():
    """Get collection names from configuration."""
    config = get_config()
    return {
        "candidates": config.candidates_collection,
        "jobs": config.jobs_collection,
    }


def generate_unique_id(phone: str) -> str:
    """
    Generate a unique hash ID from the phone number.
    """
    return hashlib.sha256(phone.encode("utf-8")).hexdigest()


def insert_candidate_to_mongo_dict(data_dict: dict) -> str:
    """Insert candidate data dict directly into MongoDB with proper error handling."""
    try:
        # Validate required fields with fallbacks
        candidate_name = data_dict.get("candidate_name", "Unknown")

        # Check for phone number with multiple possible keys
        phone_keys = ["candidate_phone", "phone", "phone_number", "contact_phone"]
        phone_number = None

        for key in phone_keys:
            if key in data_dict and data_dict[key]:
                phone_number = str(data_dict[key]).strip()
                break

        # If no phone number found, generate one based on name + timestamp for uniqueness
        if not phone_number:
            import time

            phone_number = (
                f"generated_{candidate_name.replace(' ', '_')}_{int(time.time())}"
            )
            print(
                f"⚠️ No phone number found for {candidate_name}, using generated ID: {phone_number}"
            )
            data_dict["candidate_phone"] = phone_number

        # Generate a unique ID using phone number (or generated ID)
        data_dict["_id"] = generate_unique_id(phone_number)

        # Ensure all values are properly formatted for MongoDB
        for key, value in data_dict.items():
            if isinstance(value, (list, dict)):
                data_dict[key] = json.dumps(value)  # Convert complex objects to strings

        # Connect to MongoDB
        db = get_mongo_client()
        collections = get_collection_names()
        collection = db[collections["candidates"]]

        # Insert with error handling - use upsert to handle duplicates gracefully
        try:
            # 🔍 Check if candidate already exists first - ENHANCED DUPLICATE DETECTION
            # Check by both name AND id to prevent duplicates from chunks with different phone formats
            existing_by_name = collection.find_one({"candidate_name": candidate_name})
            existing_by_id = collection.find_one({"_id": data_dict["_id"]})

            if existing_by_name or existing_by_id:
                print(
                    f"⚠️  Candidate {candidate_name} already exists in MongoDB - Skipping duplicate insertion"
                )
                return f"⚠️  Candidate {candidate_name} already exists - Skipped duplicate insertion"

            result = collection.insert_one(data_dict)
            print(f"✅ Successfully inserted new candidate data for {candidate_name}")
            return f"✅ Successfully inserted new candidate data for {candidate_name}"

        except Exception as insert_error:
            print(f"❌ Database insertion failed for {candidate_name}: {insert_error}")
            return f"❌ Database insertion failed for {candidate_name}: {insert_error}"

    except Exception as e:
        error_msg = f"Error inserting candidate: {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg


def insert_job_to_mongo_dict(data_dict: dict) -> None:
    """Insert a job posting dict directly into MongoDB.

    Args:
        data_dict: Dictionary containing job information
    """
    # Ensure required fields exist
    if "job_title" not in data_dict or "company_name" not in data_dict:
        raise ValueError("job_title and company_name are required fields")

    # Generate a unique ID using job title and company name
    unique_string = f"{data_dict['job_title']}_{data_dict['company_name']}"
    data_dict["_id"] = generate_unique_id(unique_string)

    # Ensure all values are strings
    for key, value in data_dict.items():
        if isinstance(value, (list, dict)):
            data_dict[key] = json.dumps(value)
        elif value is None:
            data_dict[key] = ""

    # Connect to MongoDB
    db = get_mongo_client()
    collections = get_collection_names()
    collection = db[collections["jobs"]]

    # Insert or update with error handling
    try:
        # 🔍 Check if job already exists first
        existing = collection.find_one({"_id": data_dict["_id"]})
        if existing:
            print(
                f"⚠️  Job '{data_dict['job_title']}' at '{data_dict['company_name']}' already exists - Skipping duplicate insertion"
            )
            return

        result = collection.insert_one(data_dict)
        print(f"✅ Job inserted with _id: {result.inserted_id}")
    except Exception as e:
        print(f"❌ Error storing job: {str(e)}")
        raise


def safe_insert_candidate(data):
    """
    Safely insert a candidate into MongoDB with enhanced error handling and automatic processing
    """
    print("\n" + "=" * 50)
    print("🔧 MongoDB Tool Called - Starting insertion process")
    print("=" * 50)

    try:
        # Parse JSON data
        print("📝 Attempting to parse JSON data...")
        if isinstance(data, str):
            candidate_data = json.loads(data)
            print("✅ JSON parsed successfully from string")
        else:
            candidate_data = data
            print("✅ Data already in dictionary format")

        print(f"📋 Received data keys: {list(candidate_data.keys())}")

        # Prepare minimal candidate data
        print("🔄 Preparing candidate data for MongoDB...")
        mongo_data = {}

        # Required field: candidate_name
        if "candidate_name" in candidate_data and candidate_data["candidate_name"]:
            mongo_data["candidate_name"] = candidate_data["candidate_name"]
            print(f"✅ Name: {mongo_data['candidate_name']}")
        else:
            print("❌ ERROR: candidate_name is required but missing!")
            return {"success": False, "error": "candidate_name is required"}

        # Optional fields with fallbacks
        if "candidate_email" in candidate_data and candidate_data["candidate_email"]:
            mongo_data["candidate_email"] = candidate_data["candidate_email"]
            print(f"✅ Email: {mongo_data['candidate_email']}")
        else:
            # Generate fallback email
            name_part = mongo_data["candidate_name"].lower().replace(" ", ".")
            mongo_data["candidate_email"] = f"{name_part}@resume.example.com"
            print(f"🔄 Generated fallback email: {mongo_data['candidate_email']}")

        if "candidate_phone" in candidate_data and candidate_data["candidate_phone"]:
            mongo_data["candidate_phone"] = candidate_data["candidate_phone"]
            print(f"✅ Phone: {mongo_data['candidate_phone']}")
        else:
            # Generate fallback phone
            import hashlib

            name_hash = hashlib.md5(mongo_data["candidate_name"].encode()).hexdigest()
            phone_digits = "".join(filter(str.isdigit, name_hash))[:10]
            mongo_data["candidate_phone"] = f"+1{phone_digits}"
            print(f"🔄 Generated fallback phone: {mongo_data['candidate_phone']}")

        # Add optional fields if present
        if "candidate_skills" in candidate_data:
            mongo_data["candidate_skills"] = candidate_data["candidate_skills"]
            print(f"✅ Skills: {len(mongo_data['candidate_skills'])} skills added")

        if "candidate_total_experience" in candidate_data:
            mongo_data["candidate_total_experience"] = candidate_data[
                "candidate_total_experience"
            ]
            print(f"✅ Experience: {mongo_data['candidate_total_experience']}")

        # Add processing timestamp
        from datetime import datetime

        mongo_data["processed_at"] = datetime.utcnow()
        mongo_data["status"] = "processed"

        print(f"📤 Final data prepared with {len(mongo_data)} fields")

        # Use existing MongoDB connection setup
        print("🔌 Connecting to MongoDB...")
        db = get_mongo_client()
        collections = get_collection_names()
        collection = db[collections["candidates"]]

        # Initialize MongoDB client
        print("🔌 Connecting to MongoDB...")
        db = get_mongo_client()
        collections = get_collection_names()
        collection = db[collections["candidates"]]

        # Generate unique ID for the candidate
        unique_id = generate_unique_id(mongo_data["candidate_phone"])
        mongo_data["_id"] = unique_id

        # 🔍 Check for duplicates by name or ID - Skip if exists
        print(f"🔍 Checking for existing candidate: {mongo_data['candidate_name']}")
        existing_by_name = collection.find_one(
            {"candidate_name": mongo_data["candidate_name"]}
        )
        existing_by_id = collection.find_one({"_id": unique_id})

        if existing_by_name or existing_by_id:
            print(
                f"⚠️  Candidate '{mongo_data['candidate_name']}' already exists in MongoDB - Skipping insertion"
            )
            return {
                "success": True,
                "message": f"Candidate {mongo_data['candidate_name']} already exists - Skipped duplicate insertion",
                "candidate_name": mongo_data["candidate_name"],
                "action": "skipped",
            }

        # Insert new candidate (no duplicates found)
        print("📤 Inserting new candidate into MongoDB...")
        result = collection.insert_one(mongo_data)
        print(f"📋 MongoDB Insert Result: ID {result.inserted_id}")

        print("=" * 50)
        print(
            f"🎉 SUCCESS: New candidate '{mongo_data['candidate_name']}' inserted successfully!"
        )
        print("=" * 50)

        return {
            "success": True,
            "message": f"Candidate {mongo_data['candidate_name']} inserted successfully",
            "candidate_name": mongo_data["candidate_name"],
            "inserted_id": str(result.inserted_id),
            "action": "inserted",
        }

    except json.JSONDecodeError as e:
        error_msg = f"JSON parsing error: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Database insertion error: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}
