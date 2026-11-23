
import os
import pandas as pd
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load the rainfall dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "rainfall_in_india_1901-2015.csv")

df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()

# Available regions and months
REGIONS = sorted(df["SUBDIVISION"].dropna().unique().tolist())
MONTHS = [
    "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
    "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
]

# API key verification
def check_api_key():
    expected_key = os.environ.get("API_SECRET_KEY")
    supplied_key = request.headers.get("X-API-Key")

    if not expected_key or supplied_key != expected_key:
        return False

    return True


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Agriculture Rainfall Prediction API is running"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "model_loaded": not df.empty
    })


@app.route("/options", methods=["GET"])
def options():
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({
        "regions": REGIONS,
        "months": MONTHS
    })


@app.route("/predict", methods=["POST"])
def predict():
    if not check_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}

    region = str(data.get("region", "")).strip()
    month = str(data.get("month", "")).strip().upper()

    if region not in REGIONS:
        return jsonify({"error": "Please select a valid region"}), 400

    if month not in MONTHS:
        return jsonify({"error": "Please select a valid month"}), 400

    region_data = df[df["SUBDIVISION"] == region]
    rainfall_values = pd.to_numeric(region_data[month], errors="coerce").dropna()

    if rainfall_values.empty:
        return jsonify({"error": "Rainfall data is not available"}), 404

    predicted_rainfall = round(float(rainfall_values.mean()), 2)

    return jsonify({
        "region": region,
        "month": month,
        "predicted_rainfall_mm": predicted_rainfall,
        "record_count": int(len(rainfall_values)),
        "method": "historical_average_1901_2015"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
