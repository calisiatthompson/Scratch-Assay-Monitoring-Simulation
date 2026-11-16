
import os
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient


# ==========================================
# DATABASE CONNECTION
# ==========================================

base_folder = Path(__file__).resolve().parent

load_dotenv(base_folder / ".env")

mongodb_uri = os.getenv("MONGODB_URI")

database_name = os.getenv(
    "MONGODB_DATABASE",
    "scratch_assay"
)

if not mongodb_uri:
    raise ValueError("MongoDB URI not found")

client = MongoClient(
    mongodb_uri,
    serverSelectionTimeoutMS=5000
)

db = client[database_name]

experiments = db["experiments"]
captures = db["captures"]


# ==========================================
# CREATE EXPERIMENT
# ==========================================

def create_experiment(experiment_id):

    document = {
        "experiment_id": experiment_id,
        "mode": "simulation",
        "treatment_group": "sample_images",
        "start_time": datetime.now(timezone.utc),
        "status": "running",
        "expected_captures": 3,
        "completed_captures": 0
    }

    experiments.insert_one(document)

    print("Experiment registered in MongoDB")


# ==========================================
# SAVE CAPTURE MEASUREMENTS
# ==========================================

def save_capture(
    experiment_id,
    record,
    original_blob,
    processed_blob
):

    document = {
        "experiment_id": experiment_id,

        "time_hours": record["hour"],

        "capture_timestamp": record["timestamp"],

        "scratch_area_px2": record["area"],

        "average_width_px": record["width"],

        "scratch_closure_percent": record["closure"],

        "original_image": original_blob,

        "processed_image": processed_blob,

        "recorded_at": datetime.now(timezone.utc)
    }

    captures.update_one(
        {
            "experiment_id": experiment_id,
            "time_hours": record["hour"]
        },
        {"$set": document},
        upsert=True
    )

    total = captures.count_documents({
        "experiment_id": experiment_id
    })

    experiments.update_one(
        {"experiment_id": experiment_id},
        {
            "$set": {
                "completed_captures": total
            }
        }
    )

    print("Capture measurements saved to MongoDB")


# ==========================================
# COMPLETE EXPERIMENT
# ==========================================

def complete_experiment(experiment_id):

    experiments.update_one(
        {"experiment_id": experiment_id},
        {
            "$set": {
                "status": "completed",
                "end_time": datetime.now(timezone.utc)
            }
        }
    )

    print("Experiment marked as completed")


# ==========================================
# TEST DATABASE CONNECTION
# ==========================================

if __name__ == "__main__":

    print("Connecting to MongoDB...")

    client.admin.command("ping")

    print("MongoDB connection successful!")
    print("Database:", database_name)

    print("Collections:", db.list_collection_names())
