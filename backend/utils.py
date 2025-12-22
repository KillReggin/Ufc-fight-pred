import pandas as pd

def load_profiles(path):
    if not path.exists():
        raise FileNotFoundError(f"Profiles not found: {path}")

    df = pd.read_parquet(path)

    if "name" in df.columns:
        df["name"] = df["name"].astype(str).str.lower().str.strip()
        df = df.set_index("name")
    else:
        df.index = df.index.map(lambda x: str(x).lower().strip())

    return df


def find_fighter(df, name: str):
    name = name.lower().strip()

    if name in df.index:
        fighter = df.loc[name]
        if isinstance(fighter, pd.DataFrame):
            return fighter.iloc[0]  
        return fighter

    matches = [idx for idx in df.index if name in idx]
    if len(matches) == 1:
        fighter = df.loc[matches[0]]
        if isinstance(fighter, pd.DataFrame):
            return fighter.iloc[0]
        return fighter

    return None


def build_input_vector(f1, f2, feature_order):
    row = {}

    numeric_fields = [
        "Ht.", "Wt.", "Reach",
        "fight_count", "winrate",
        "avg_kd", "avg_str", "avg_td",
        "avg_sub", "avg_ctrl", "avg_sig",
        "last_winrate", "last_avg_str",
        "elo",
    ]

    finish_fields = [
        "finish_rate",
        "pct_finish_r1",
        "pct_finish_r2",
        "pct_finish_r3p",
        "avg_finish_round",
    ]

    for field in finish_fields:
        r = float(f1.get(field, 0) or 0)
        b = float(f2.get(field, 0) or 0)

        row[f"R_{field}"] = r
        row[f"B_{field}"] = b
        row[f"DIFF_{field}"] = r - b

    for field in numeric_fields:
        r = float(f1.get(field, 0) or 0)
        b = float(f2.get(field, 0) or 0)

        row[f"R_{field}"] = r
        row[f"B_{field}"] = b
        row[f"DIFF_{field}"] = r - b

    stances = ["Orthodox", "Southpaw", "Switch", "Sideways", "Unknown"]
    for s in stances:
        row[f"R_Stance_{s}"] = 1 if str(f1.get("Stance", "Unknown")) == s else 0
        row[f"B_Stance_{s}"] = 1 if str(f2.get("Stance", "Unknown")) == s else 0

    weight_classes = [
        "Catch Weight", "Featherweight", "Flyweight", "Heavyweight",
        "Light Heavyweight", "Lightweight", "Middleweight",
        "Welterweight", "Women's Strawweight"
    ]
    for wc in weight_classes:
        row[f"Weight_Class_{wc}"] = 1 if str(f1.get("Weight_Class", "")) == wc else 0

    styles = ["No Clear Style", "Striker", "Wrestler", "Unknown"]
    for st in styles:
        row[f"R_Fighting Style_{st}"] = 1 if str(f1.get("Fighting Style", "Unknown")) == st else 0
        row[f"B_Fighting Style_{st}"] = 1 if str(f2.get("Fighting Style", "Unknown")) == st else 0

    X = pd.DataFrame([row])

    for col in feature_order:
        if col not in X.columns:
            X[col] = 0

    return X[feature_order]
