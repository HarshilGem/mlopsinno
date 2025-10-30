from flask import Flask, request, jsonify, send_from_directory
import joblib
import pandas as pd
import waitress
import os
import requests
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import mlflow
import mlflow.tracking
import psutil
import time

# MLflow configuration (use compose service name inside containers)
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
MLFLOW_EXPERIMENT = os.getenv('MLFLOW_EXPERIMENT', 'rf_jamming_docker')
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
try:
    exp = mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT)
    if exp is None:
        FRONTEND_EXPERIMENT_ID = mlflow.create_experiment(MLFLOW_EXPERIMENT)
        print(f"Created MLflow experiment '{MLFLOW_EXPERIMENT}' id={FRONTEND_EXPERIMENT_ID}", flush=True)
    else:
        FRONTEND_EXPERIMENT_ID = exp.experiment_id
        print(f"Using existing MLflow experiment '{MLFLOW_EXPERIMENT}' id={FRONTEND_EXPERIMENT_ID}", flush=True)
except Exception as e:
    print('MLflow init failed in frontend:', e, flush=True)
    FRONTEND_EXPERIMENT_ID = None


# Paths (model and scaler stay at project root)
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
MODEL_PATH = os.path.join(PROJECT_ROOT, 'rf_jamming_model.pkl')
SCALER_PATH = os.path.join(PROJECT_ROOT, 'scaler.pkl')
COLUMNS = ["Time", "SNR", "Speed", "RSSI", "PDR", "Relative_Speed"]


app = Flask(__name__, static_folder='static', static_url_path='')
# Metrics
REQUEST_COUNT = Counter('frontend_http_requests_total', 'Total HTTP requests', ['endpoint', 'method', 'http_status'])
REQUEST_LATENCY = Histogram('frontend_http_request_duration_seconds', 'Request latency', ['endpoint', 'method'])


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
    from time import perf_counter
    start = perf_counter()
    data = request.get_json(force=True, silent=True)
    if data is None:
        data = request.form.to_dict()

    # Validate and build a single-row DataFrame
    try:
        row = [float(data.get(col)) for col in COLUMNS]
    except Exception as e:
        status = 400
        REQUEST_COUNT.labels('/predict', request.method, str(status)).inc()
        REQUEST_LATENCY.labels('/predict', request.method).observe(perf_counter() - start)
        return jsonify({'error': 'Invalid input. Ensure all fields are provided and numeric.', 'details': str(e)}), status

    df = pd.DataFrame([dict(zip(COLUMNS, row))])

    try:
        X = scaler.transform(df)
        pred = model.predict(X)
    except Exception as e:
        status = 500
        REQUEST_COUNT.labels('/predict', request.method, str(status)).inc()
        REQUEST_LATENCY.labels('/predict', request.method).observe(perf_counter() - start)
        return jsonify({'error': 'Model prediction failed', 'details': str(e)}), status

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

    # MLflow tracking: start run in the intended experiment and log system metrics
    try:
        run_kwargs = {'run_name': 'predict'}
        if FRONTEND_EXPERIMENT_ID is not None:
            run_kwargs['experiment_id'] = FRONTEND_EXPERIMENT_ID
        with mlflow.start_run(**run_kwargs):
            mlflow.log_params({'Time': row[0], 'SNR': row[1], 'Speed': row[2], 'RSSI': row[3], 'PDR': row[4], 'Relative_Speed': row[5]})
            mlflow.log_metric('prediction', float(prediction_value))
            # system metrics
            try:
                mlflow.log_metric('cpu_percent', psutil.cpu_percent(interval=0.1))
                mlflow.log_metric('memory_percent', psutil.virtual_memory().percent)
            except Exception:
                pass
            # store input payload as artifact
            try:
                mlflow.log_dict(payload, 'input.json')
            except Exception:
                pass
    except Exception as e:
        print(f"MLflow logging failed in frontend: {e}", flush=True)

    status = 200
    REQUEST_COUNT.labels('/predict', request.method, str(status)).inc()
    REQUEST_LATENCY.labels('/predict', request.method).observe(perf_counter() - start)
    return jsonify({'prediction': prediction_value}), status


@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    # Log the model artifact once at startup (non-blocking)
    try:
        if FRONTEND_EXPERIMENT_ID is not None:
            with mlflow.start_run(run_name='model_import_startup', experiment_id=FRONTEND_EXPERIMENT_ID):
                try:
                    mlflow.log_artifact(MODEL_PATH, artifact_path='model')
                except Exception as e:
                    print('Failed to log model artifact at startup:', e, flush=True)
                # small delay to allow logs to flush
                time.sleep(0.25)
    except Exception as e:
        print('Startup MLflow model logging failed:', e, flush=True)
    waitress.serve(app, host='0.0.0.0', port=port)


