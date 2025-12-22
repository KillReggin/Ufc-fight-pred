import json
import joblib
import pandas as pd
import shap
from pathlib import Path
import numpy as np
import math

from feature_labels import FEATURE_LABELS
from utils import load_profiles, find_fighter, build_input_vector

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "model.joblib"
FEATURES_PATH = BASE_DIR / "models" / "feature_names.json"
PROFILES_PATH = BASE_DIR / "data" / "fighters_profiles.parquet"
FIGHTERS_CSV = BASE_DIR / "data" / "raw" / "Fighters.csv"

model = joblib.load(MODEL_PATH)

with open(FEATURES_PATH) as f:
    FEATURE_ORDER = json.load(f)

profiles = load_profiles(PROFILES_PATH)

fighters_df = pd.read_csv(FIGHTERS_CSV)
fighters_df["full_name"] = fighters_df["full_name"].str.lower().str.strip()
fighters_df = fighters_df.set_index("full_name")

explainer = shap.TreeExplainer(model)

def pretty_feature(name):
    return FEATURE_LABELS.get(name, name)


def clean_value(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, (np.integer, np.floating)):
        return float(v)
    return v


def clean_dict(d):
    return {k: clean_value(v) for k, v in d.items()}


def get_fighter_card(name: str):
    key = name.lower().strip()

    if key not in fighters_df.index:
        return {
            "name": name,
            "nickname": "",
            "record": "-",
            "height": "-",
            "reach": "-",
            "stance": "-",
            "weight": "-"
        }

    row = fighters_df.loc[key]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]

    card = {
        "name": name,
        "nickname": row.get("nickname") or "",
        "record": f'{row.get("wins")}-{row.get("losses")}-{row.get("draws")}',
        "height": row.get("height"),
        "reach": row.get("reach"),
        "stance": row.get("stance"),
        "weight": row.get("weight"),
    }

    return clean_dict(card)


def predict_fight(f1_name: str, f2_name: str):
    f1 = find_fighter(profiles, f1_name)
    f2 = find_fighter(profiles, f2_name)

    if f1 is None or f2 is None:
        raise ValueError("Fighter not found")

    X = build_input_vector(f1, f2, FEATURE_ORDER)

    proba_red = float(model.predict_proba(X)[0][1])
    proba_blue = 1.0 - proba_red

    winner = f1_name if proba_red >= 0.5 else f2_name

    shap_vals = explainer.shap_values(X)
    sv = shap_vals[1][0] if isinstance(shap_vals, list) else shap_vals[0]

    top_indices = np.argsort(np.abs(sv))[-10:][::-1]

    shap_features = [
        {
            "feature": pretty_feature(FEATURE_ORDER[i]),
            "value": round(float(sv[i]), 4)
        }
        for i in top_indices
    ]

    return {
        "fighter_1": get_fighter_card(f1_name),  
        "fighter_2": get_fighter_card(f2_name),  

        "winner": winner,

        "probability": {
            "red": round(proba_red, 3),
            "blue": round(proba_blue, 3)
        },

        "shap": shap_features
    }
