import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

# load env
load_dotenv(".env")

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db["events_raw"]


def extract_events():
      """
      extract raw events from MongoDB
      """
      data = list(collection.find({}, {"_id": 0}))
      df = pd.DataFrame(data)
      return df
      
def main():
      df = extract_events()
      
      print("Total raw events:",len(df))
      
      #split by event type
      orders = df[df["event_type"] == "historical_order"]
      payments = df[df["event_type"] == "historical_payment"]
      refunds = df[df["event_type"] == "historical_refund"]
      shipments = df[df["event_type"] == "historical_shipment"]
      
      print("orders:", len(orders))
      print("payments:", len(payments))
      print("refunds:", len(refunds))
      print("shipments:", len(shipments))
      
      #expand payloads into structured columns
      orders_expanded = pd.json_normalize(orders["payload"])
      
      # select useful column (adjust based on what exists in your JSON)
      orders_clean = orders_expanded.copy()
      
      # replace dot with underscore for BigQuery compartibility
      orders_clean.columns = orders_clean.columns.str.replace(".", "_", regex=False)
      
      # remove duplicate column safely
      orders_clean = orders_clean.loc[:, ~orders_clean.columns.duplicated()]
      
      # covert datetime columns if they exist
      if "created_at" in orders_clean.columns:
         orders_clean["created_at"] = pd.to_datetime(orders_clean["created_at"], errors="coerce")
         
         
      # covert numeric columns safely
      for col in orders_clean.columns:
         if "amount" in col or "price" in col:
            orders_clean[col] = pd.to_numeric(orders_clean[col], errors="coerce")
            
      print("\nClean Orders Table:,")
      print(orders_clean.head())

      payments_expanded = pd.json_normalize(payments["payload"])
      refunds_expanded = pd.json_normalize(refunds["payload"])
      shipments_expanded = pd.json_normalize(shipments["payload"])
      payments_expanded.columns = payments_expanded.columns.str.replace(".", "_", regex=False)
      refunds_expanded.columns = refunds_expanded.columns.str.replace(".", "_", regex=False)
      shipments_expanded.columns = shipments_expanded.columns.str.replace(".", "_", regex=False)
      
      # remove duplicate columns safely
      payments_expanded = payments_expanded.loc[:, ~payments_expanded.columns.duplicated()]
      refunds_expanded = refunds_expanded.loc[:, ~refunds_expanded.columns.duplicated()]
      shipments_expanded = shipments_expanded.loc[:, ~shipments_expanded.columns.duplicated()]

      print("\nsample clean orders:")
      print(orders_expanded.head())
      
      orders_clean.to_csv("data/orders_clean.csv", index=False)
      payments_expanded.to_csv("data/payments_clean.csv", index=False)
      refunds_expanded.to_csv("data/refunds_clean.csv", index=False)
      shipments_expanded.to_csv("data/shipments_clean,csv", index=False)
      
      print("\nClean CSV files saved.")
      
      # ===== SIMPLE KPI CHECKS =====

      print("\n===== BASIC METRICS =====")

      print("Total Orders:", len(orders_clean))

      if "amount" in orders_clean.columns:
         print("Total Order Revenue:", orders_clean["amount"].sum())

      if "amount" in refunds_expanded.columns:
         print("Total Refund Amount:", refunds_expanded["amount"].sum())

      print("Total Payments:", len(payments_expanded))
      print("Total Shipments:", len(shipments_expanded))
      
if __name__=="__main__":
   main()