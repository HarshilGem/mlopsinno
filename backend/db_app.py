from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, request
from waitress import serve
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import os
import mlflow


# MLflow configuration (when running under docker-compose use service name and port)
# MLflow configuration (when running under docker-compose use service name and port)
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
MLFLOW_EXPERIMENT = os.getenv('MLFLOW_EXPERIMENT', 'rf_jamming_docker')
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
# Ensure experiment exists on the tracking server and get its id. Use experiment_id when starting runs
try:
    exp = mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT)
    if exp is None:
        experiment_id = mlflow.create_experiment(MLFLOW_EXPERIMENT)
        print(f"Created MLflow experiment '{MLFLOW_EXPERIMENT}' id={experiment_id}", flush=True)
    else:
        experiment_id = exp.experiment_id
        print(f"Using existing MLflow experiment '{MLFLOW_EXPERIMENT}' id={experiment_id}", flush=True)
    print(f"MLflow tracking URI: {mlflow.get_tracking_uri()}", flush=True)
except Exception as e:
    print("MLflow init failed:", e, flush=True)
    experiment_id = None

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///rf_predictions.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Metrics
REQUEST_COUNT = Counter('backend_http_requests_total', 'Total HTTP requests', ['endpoint', 'method', 'http_status'])
REQUEST_LATENCY = Histogram('backend_http_request_duration_seconds', 'Request latency', ['endpoint', 'method'])


class RFPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Time = db.Column(db.Float, nullable=False)
    SNR = db.Column(db.Float, nullable=False)
    Speed = db.Column(db.Float, nullable=False)
    RSSI = db.Column(db.Float, nullable=False)
    PDR = db.Column(db.Float, nullable=False)
    Relative_Speed = db.Column(db.Float, nullable=False)
    prediction = db.Column(db.String(50), nullable=False)


@app.route('/add_record', methods=['POST'])
def add_record():
    from time import perf_counter
    start = perf_counter()
    data = request.get_json()
    required = ['Time', 'SNR', 'Speed', 'RSSI', 'PDR', 'Relative_Speed', 'prediction']
    if not data or not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields', 'required': required}), 400

    try:
        new_record = RFPrediction(
            Time=float(data['Time']),
            SNR=float(data['SNR']),
            Speed=float(data['Speed']),
            RSSI=float(data['RSSI']),
            PDR=float(data['PDR']),
            Relative_Speed=float(data['Relative_Speed']),
            prediction=str(data['prediction'])
        )
    except Exception as e:
        return jsonify({'error': 'Invalid types for one or more fields', 'details': str(e)}), 400

    db.session.add(new_record)
    db.session.commit()
    status = 201
    # Log this prediction as an MLflow run (one run per saved record)
    try:
        # start run in the intended experiment when available
        run_kwargs = {'run_name': f"pred_{new_record.id}"}
        if experiment_id is not None:
            run_kwargs['experiment_id'] = experiment_id
        with mlflow.start_run(**run_kwargs):
            # log input features as params
            mlflow.log_params({
                'Time': float(new_record.Time),
                'SNR': float(new_record.SNR),
                'Speed': float(new_record.Speed),
                'RSSI': float(new_record.RSSI),
                'PDR': float(new_record.PDR),
                'Relative_Speed': float(new_record.Relative_Speed),
            })
            # log prediction as metric if numeric, otherwise as param
            try:
                mlflow.log_metric('prediction', float(new_record.prediction))
            except Exception:
                mlflow.log_param('prediction', str(new_record.prediction))
    except Exception as e:
        # log the failure so it's easier to debug
        print('MLflow logging failed:', e, flush=True)
    REQUEST_COUNT.labels('/add_record', request.method, str(status)).inc()
    REQUEST_LATENCY.labels('/add_record', request.method).observe(perf_counter() - start)
    return jsonify({'message': 'Record added', 'id': new_record.id}), status


@app.route('/get_records')
def get_records():
    from time import perf_counter
    start = perf_counter()
    all_records = RFPrediction.query.all()
    records = [{
        'id': r.id,
        'Time': r.Time,
        'SNR': r.SNR,
        'Speed': r.Speed,
        'RSSI': r.RSSI,
        'PDR': r.PDR,
        'Relative_Speed': r.Relative_Speed,
        'prediction': r.prediction
    } for r in all_records]
    resp = jsonify(records)
    REQUEST_COUNT.labels('/get_records', request.method, '200').inc()
    REQUEST_LATENCY.labels('/get_records', request.method).observe(perf_counter() - start)
    return resp


@app.route('/records_page')
def records_page():
    from time import perf_counter
    start = perf_counter()
    all_records = RFPrediction.query.all()
    # Minimal HTML table rendering for quick inspection
    rows = []
    header = (
        '<tr>'
        '<th>ID</th><th>Time</th><th>SNR</th><th>Speed</th><th>RSSI</th>'
        '<th>PDR</th><th>Relative_Speed</th><th>Prediction</th>'
        '</tr>'
    )
    for r in all_records:
        rows.append(
            f"<tr><td>{r.id}</td><td>{r.Time}</td><td>{r.SNR}</td><td>{r.Speed}</td>"
            f"<td>{r.RSSI}</td><td>{r.PDR}</td><td>{r.Relative_Speed}</td><td>{r.prediction}</td></tr>"
        )

    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>RF Predictions</title>"
        "<style>body{font-family:Segoe UI,Roboto,Arial;margin:20px}table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #ddd;padding:8px;font-size:14px}th{background:#f5f5f5;text-align:left}"
        "tr:nth-child(even){background:#fafafa}</style></head><body>"
        "<h2>Stored RF Predictions</h2>"
        f"<table>{header}{''.join(rows)}</table>"
        "</body></html>"
    )
    REQUEST_COUNT.labels('/records_page', request.method, '200').inc()
    REQUEST_LATENCY.labels('/records_page', request.method).observe(perf_counter() - start)
    return html


@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.getenv('PORT', '5001'))
    print("✅ DB service running at 0.0.0.0:" + str(port))
    serve(app, host="0.0.0.0", port=port)


