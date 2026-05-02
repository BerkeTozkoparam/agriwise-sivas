"""
Model Eğitimi ve Tahmin Modülü
AgriWise Sivas — Anadolu Hackathon 2026

Görevler:
  1. Zirai don seviyesi sınıflandırması (5 sınıf) — XGBoost
  2. Hava koşulu tahmini (weather_condition) — LightGBM
  3. Genel tarım uygunluk skoru tahmini (regresyon) — XGBoost
"""

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report, accuracy_score,
    mean_absolute_error, f1_score
)

try:
    import xgboost as xgb
    XGB_OK = True
except ImportError:
    XGB_OK = False

try:
    import lightgbm as lgb
    LGB_OK = True
except ImportError:
    LGB_OK = False

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "agriwise_model_dataset.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# ── Özellik sütunları ──────────────────────────────────────────────
FEATURES = [
    "temperature_c", "humidity_pct", "wind_speed_kmh", "wind_gust_kmh",
    "precipitation_mm", "cloud_cover_pct", "visibility_km",
    "uv_index", "is_thunderstorm",
    "hour_of_day", "month",
    "temp_min_c", "temp_max_c", "total_precipitation_mm",
    "snow_hours", "rain_hours", "max_wind_kmh", "thunderstorm_occurred",
]

CAT_FEATURES = ["season", "climate_zone", "precipitation_type", "dominant_condition"]

DON_ORDER = {"YOK": 0, "DÜŞÜK": 1, "ORTA": 2, "YÜKSEK": 3, "KRİTİK": 4}
DON_LABELS = ["YOK", "DÜŞÜK", "ORTA", "YÜKSEK", "KRİTİK"]


def load_data():
    df = pd.read_csv(DATA_PATH)

    # Kategorik encoding
    le_dict = {}
    for col in CAT_FEATURES:
        if col in df.columns:
            le = LabelEncoder()
            df[col + "_enc"] = le.fit_transform(df[col].astype(str))
            le_dict[col] = le

    # Don seviyesi → sayısal
    df["don_label"] = df["zirai_don_seviyesi"].map(DON_ORDER)

    all_features = FEATURES + [c + "_enc" for c in CAT_FEATURES if c in df.columns]
    return df, all_features, le_dict


def train_don_model(df, features):
    """Zirai don seviyesi sınıflandırıcı."""
    X = df[features]
    y = df["don_label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    if XGB_OK:
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            use_label_encoder=False,
            eval_metric="mlogloss",
            random_state=42,
            verbosity=0,
        )
    else:
        model = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1  = f1_score(y_test, y_pred, average="weighted")

    print(f"\n[Don Modeli] Accuracy: {acc:.3f} | F1 (weighted): {f1:.3f}")
    print(classification_report(y_test, y_pred, target_names=DON_LABELS))

    joblib.dump(model, os.path.join(MODEL_DIR, "don_model.pkl"))
    return model, {"accuracy": acc, "f1": f1}


def train_suitability_model(df, features):
    """Genel tarım uygunluk skoru regresyonu (0-10)."""

    # Skoru don seviyesinden türet (don yoksa outdoor suitability yüksek)
    don_to_score = {"YOK": 8.0, "DÜŞÜK": 6.0, "ORTA": 4.0, "YÜKSEK": 2.0, "KRİTİK": 0.5}
    df = df.copy()
    df["agri_score"] = df["zirai_don_seviyesi"].map(don_to_score)

    # Yağış etkisi
    df["agri_score"] -= (df["precipitation_mm"].clip(0, 20) / 20) * 2
    df["agri_score"] -= (df["wind_speed_kmh"].clip(0, 60) / 60) * 1.5
    df["agri_score"] = df["agri_score"].clip(0, 10)

    X = df[features]
    y = df["agri_score"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    if XGB_OK:
        model = xgb.XGBRegressor(
            n_estimators=200, max_depth=5,
            learning_rate=0.1, random_state=42, verbosity=0
        )
    else:
        model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)

    model.fit(X_train, y_train)
    mae = mean_absolute_error(y_test, model.predict(X_test))
    print(f"\n[Suitability Modeli] MAE: {mae:.3f}")

    joblib.dump(model, os.path.join(MODEL_DIR, "suitability_model.pkl"))
    return model, {"mae": mae}


def train_all():
    print("Veri yükleniyor...")
    df, features, le_dict = load_data()
    print(f"  {len(df)} satır, {len(features)} özellik")

    print("\nZirai don modeli eğitiliyor...")
    don_model, don_metrics = train_don_model(df, features)

    print("\nSuitability modeli eğitiliyor...")
    suit_model, suit_metrics = train_suitability_model(df, features)

    joblib.dump({"features": features, "le_dict": le_dict}, os.path.join(MODEL_DIR, "meta.pkl"))
    print("\n✅ Tüm modeller kaydedildi → models/")
    return don_model, suit_model, features, le_dict


def load_models():
    don_model  = joblib.load(os.path.join(MODEL_DIR, "don_model.pkl"))
    suit_model = joblib.load(os.path.join(MODEL_DIR, "suitability_model.pkl"))
    meta       = joblib.load(os.path.join(MODEL_DIR, "meta.pkl"))
    return don_model, suit_model, meta["features"], meta["le_dict"]


def predict(input_dict, don_model, suit_model, features, le_dict):
    """
    Tek bir gözlem için tahmin yapar.
    input_dict: ham hava verisi dict'i
    """
    row = {}
    for f in FEATURES:
        row[f] = float(input_dict.get(f, 0))

    for col in CAT_FEATURES:
        le = le_dict.get(col)
        val = str(input_dict.get(col, ""))
        if le is not None:
            try:
                enc = le.transform([val])[0]
            except ValueError:
                enc = 0
            row[col + "_enc"] = enc

    X = pd.DataFrame([row])[features]
    don_label   = int(don_model.predict(X)[0])
    don_proba   = don_model.predict_proba(X)[0]
    suit_score  = float(suit_model.predict(X)[0])

    return {
        "don_seviyesi": DON_LABELS[don_label],
        "don_skoru":    round(don_proba[don_label] * 100, 1),
        "don_olasilik": {DON_LABELS[i]: round(p * 100, 1) for i, p in enumerate(don_proba)},
        "tarim_uygunluk": round(min(max(suit_score, 0), 10), 2),
    }


if __name__ == "__main__":
    train_all()
