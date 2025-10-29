from flask import Flask, request, jsonify, send_from_directory
import joblib
import pandas as pd
import waitress
import os
import requests


# Paths (model and scaler stay at project root)
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
MODEL_PATH = os.path.join(PROJECT_ROOT, 'rf_jamming_model.pkl')
SCALER_PATH = os.path.join(PROJECT_ROOT, 'scaler.pkl')
COLUMNS = ["Time", "SNR", "Speed", "RSSI", "PDR", "Relative_Speed"]


app = Flask(__name__, static_folder='static', static_url_path='')


# Load model and scaler at startup
try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
except Exception as e:
    raise RuntimeError(f"Failed to load model or scaler: {e}")


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/predict', methods=['POST'])
def predict():
    """Accepts JSON body with the feature names and returns model prediction.
    Expected JSON keys: Time, SNR, Speed, RSSI, PDR, Relative_Speed
    """
    data = request.get_json(force=True, silent=True)
    if data is None:
        data = request.form.to_dict()

    # Validate and build a single-row DataFrame
    try:
        row = [float(data.get(col)) for col in COLUMNS]
    except Exception as e:
        return jsonify({'error': 'Invalid input. Ensure all fields are provided and numeric.', 'details': str(e)}), 400

    df = pd.DataFrame([dict(zip(COLUMNS, row))])

    try:
        X = scaler.transform(df)
        pred = model.predict(X)
    except Exception as e:
        return jsonify({'error': 'Model prediction failed', 'details': str(e)}), 500

    prediction_value = str(pred[0])

    # Best-effort: save to backend DB service if available
    try:
        payload = {
            'Time': row[0],
            'SNR': row[1],
            'Speed': row[2],
            'RSSI': row[3],
            'PDR': row[4],
            'Relative_Speed': row[5],
            'prediction': prediction_value
        }
        db_service_url = os.getenv('DB_SERVICE_URL', 'http://backend:5001')
        requests.post(f"{db_service_url.rstrip('/')}/add_record", json=payload, timeout=2)
    except Exception:
        # Ignore DB errors to keep prediction endpoint responsive
        pass

    return jsonify({'prediction': prediction_value})


if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    waitress.serve(app, host='0.0.0.0', port=port)


