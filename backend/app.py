from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
import pandas as pd
import redis
import json
import hashlib

from rabbitmq import send_predict_task

BASE_DIR = Path(__file__).resolve().parent
FRONT_DIR = BASE_DIR.parent / "front"
FIGHTS_CSV = BASE_DIR / "data" / "raw" / "fights.csv"

fights_df = pd.read_csv(FIGHTS_CSV)

fights_df["Fighter_1"] = fights_df["Fighter_1"].str.lower().str.strip()
fights_df["Fighter_2"] = fights_df["Fighter_2"].str.lower().str.strip()

redis_client = redis.Redis(
    host="localhost",
    port=10004,
    db=0,
    decode_responses=True
)

CACHE_TTL = 60 * 10  


def make_cache_key(f1: str, f2: str) -> str:
    key = f"{f1.lower().strip()}__vs__{f2.lower().strip()}"
    return "predict:" + hashlib.md5(key.encode()).hexdigest()


def normalize_method(method: str) -> str:
    m = method.lower()
    if "ko" in m or "tko" in m:
        return "KO/TKO"
    if "sub" in m:
        return "SUB"
    if "dec" in m:
        return "DEC"
    return method.upper()


def determine_winner(row):
    score_1 = (
        row["KD_1"] * 10 +
        row["STR_1"] +
        row["TD_1"] * 5 +
        row["SUB_1"] * 5 +
        row["Ctrl_1"] * 0.1
    )

    score_2 = (
        row["KD_2"] * 10 +
        row["STR_2"] +
        row["TD_2"] * 5 +
        row["SUB_2"] * 5 +
        row["Ctrl_2"] * 0.1
    )

    if score_1 >= score_2:
        return row["Fighter_1"], row["Fighter_2"]
    else:
        return row["Fighter_2"], row["Fighter_1"]

app = Flask(__name__, static_folder=str(FRONT_DIR))
CORS(app)

print("FRONT_DIR:", FRONT_DIR)
print("Files:", list(FRONT_DIR.iterdir()))


@app.route("/")
def index():
    return send_from_directory(FRONT_DIR, "index.html")


@app.route("/comparison.html")
def comparison():
    return send_from_directory(FRONT_DIR, "comparison.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(FRONT_DIR, path)


@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.json
    f1 = data["fighter1"]
    f2 = data["fighter2"]

    cache_key = make_cache_key(f1, f2)
    lock_key = cache_key + ":lock"

    cached = redis_client.get(cache_key)
    if cached:
        print("⚡ REDIS HIT")
        return jsonify(json.loads(cached)), 200

    lock_acquired = redis_client.set(
        lock_key,
        "1",
        ex=30,  
        nx=True
    )

    if lock_acquired:
        print("🔒 LOCK ACQUIRED → send task")
        send_predict_task({
            "fighter1": f1,
            "fighter2": f2
        })
    else:
        print("⏳ LOCK EXISTS → waiting")

    return jsonify({"status": "processing"}), 202

@app.route("/api/fighter-history/<name>")
def fighter_history(name):
    key = name.lower().strip()

    df = fights_df[
        (fights_df["Fighter_1"] == key) |
        (fights_df["Fighter_2"] == key)
    ].head(5)

    history = []

    for _, row in df.iterrows():
        winner, loser = determine_winner(row)

        if key == winner:
            result = "WIN"
            opponent = loser
        else:
            result = "LOSS"
            opponent = winner

        history.append({
            "result": result,
            "opponent": opponent.title(),
            "method": normalize_method(row["Method"]),
            "round": int(row["Round"]),
            "time": row["Fight_Time"]
        })

    return jsonify(history)

if __name__ == "__main__":
    app.run(port=8000, debug=True)
