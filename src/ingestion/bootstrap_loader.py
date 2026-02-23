import os
import json
import hashlib
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv



# Load environment variables
load_dotenv(dotenv_path=".env")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db["events_raw"]


def generate_event_id(record, event_type):
    unique_string = json.dumps(record, sort_keys=True)
    base_string = f"{event_type}-{unique_string}"
    return hashlib.sha256(base_string.encode("utf-8")).hexdigest()


def wrap_as_event(record, event_type):
    """
    wrap raw record as synthetic event
    """
    event_time = (
    record.get("event_time")
    or record.get("created_at")
    or datetime.now(timezone.utc).isoformat()
)

    return {
        "event_id": generate_event_id(record, event_type),
        "event_type": event_type,
        "event_time": event_time,
        "vendor": record.get("vendor", "unknown"),
        "payload": record,
        "ingested_at":datetime.now(timezone.utc)
    }
    
def load_json_file(filepath, event_type):
    print(f"processing {filepath}...")
    
    with open(filepath,"r") as file:
        data = json.load(file)
        
        for record in data:
            event_document = wrap_as_event(record, event_type)
            
            collection.update_one(
                {"event_id": event_document["event_id"]},
                {"$set": event_document},
                upsert=True
            )
            
    print(f"Finished loading {filepath}")
    
    
def main():
    bootstrap_path = "data/bootstrap"
    
    files = {
        "orders_2023.json": "historical_order",
        "payments_2023.json": "historical_payment",
        "shipments_2023.json": "historical_shipment",
        "refunds_2023.json": "historical_refund"
    }
        
    for filename, event_type in files.items():
        filepath = os.path.join(bootstrap_path, filename)
        load_json_file(filepath, event_type)


    print("Bootstrap loading complete!")
    
    
if __name__== "__main__":
    main()
    
print("Total documents:",
collection.count_documents({}))

# collection.delete_many({})
