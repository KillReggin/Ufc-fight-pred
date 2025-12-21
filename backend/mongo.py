from pymongo import MongoClient
from datetime import datetime

MONGO_URI = "mongodb://root:secret@localhost:10003/?authSource=admin"

client = MongoClient(MONGO_URI)
db = client["ufc_ml"]

predictions = db["predictions"]


def save_prediction(result: dict):
    doc = {
        "fighter_red": result["fighter_1"]["name"],
        "fighter_blue": result["fighter_2"]["name"],
        "winner": result["winner"],
        "probability": result["probability"],
        "shap_top": result["shap"][:10],
        "model_version": "lgbm_v1.0",
        "created_at": datetime.utcnow()
    }
    predictions.insert_one(doc)