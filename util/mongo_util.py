# importing module
from pymongo import MongoClient, errors
from autogen_core.tools import FunctionTool
from config.constants import hostname, database, port
import json
import hashlib
import os


collection_name_of_resumes = "candidates"
collection_name_of_job = "job"


def get_mongo_uri():
    uri = (
        "mongodb://"
        + os.getenv("DB_USERNAME")
        + ":"
        + os.getenv("DB_PASSWORD")
        + "@"
        + hostname
        + ":"
        + port
        + "/"
        + database
    )
    return uri


def get_mongo_client():
    # Connect with the portnumber and host
    client = MongoClient(get_mongo_uri())
    # Access database
    mydatabase = client[database]
    return mydatabase


def generate_unique_id(phone: str) -> str:
    """
    Generate a unique hash ID from the phone number.
    """
    return hashlib.sha256(phone.encode("utf-8")).hexdigest()


def insert_candidate_to_mongo(data: str) -> None:
    # Parse the JSON string into a dictionary
    data_dict = json.loads(data)

    # Generate a unique ID using phone number and set as _id
    if "candidate_phone" not in data_dict:
        raise ValueError("Phone number not found in JSON.")

    data_dict["_id"] = generate_unique_id(data_dict["candidate_phone"])

    # Connect to MongoDB
    db = get_mongo_client()
    collection = db[collection_name_of_resumes]
    # Insert with error handling to avoid duplicates
    try:
        result = collection.insert_one(data_dict)
        print(f"Candidate inserted with _id: {result.inserted_id}")
    except errors.DuplicateKeyError:
        print("Duplicate candidate found. Document not inserted.")


def insert_job_to_mongo(data: str) -> None:
    """Insert a job posting into MongoDB.

    Args:
        data: JSON string containing job information
    """
    # Parse the JSON string into a dictionary
    try:
        data_dict = json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")

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
    collection = db[collection_name_of_job]

    # Insert or update with error handling
    try:
        result = collection.replace_one(
            {"_id": data_dict["_id"]}, data_dict, upsert=True
        )
        if result.upserted_id:
            print(f"✅ Job inserted with _id: {result.upserted_id}")
        else:
            print(f"✅ Job updated with _id: {data_dict['_id']}")
    except Exception as e:
        print(f"❌ Error storing job: {str(e)}")
        raise
