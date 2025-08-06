# importing module
from pymongo import MongoClient, errors
from config.constants import hostname, database, port
import json
import hashlib
import os


collection_name_of_resumes = "candidates"


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


def insert_candidate_to_mongo(json_path):
    # Load JSON data
    with open(json_path, "r") as file:
        data = json.load(file)

    # Generate a unique ID using phone number and set as _id
    if "phone" not in data:
        raise ValueError("Phone number not found in JSON.")

    data["_id"] = generate_unique_id(data["phone"])

    # Connect to MongoDB
    db = get_mongo_client()
    collection = db[collection_name_of_resumes]
    # Insert with error handling to avoid duplicates
    try:
        result = collection.insert_one(data)
        print(f"Candidate inserted with _id: {result.inserted_id}")
    except errors.DuplicateKeyError:
        print("Duplicate candidate found. Document not inserted.")
