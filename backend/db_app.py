from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, request
from waitress import serve
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///rf_predictions.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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
    return jsonify({'message': 'Record added', 'id': new_record.id}), 201


@app.route('/get_records')
def get_records():
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
    return jsonify(records)


@app.route('/records_page')
def records_page():
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
    return html


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.getenv('PORT', '5001'))
    print("✅ DB service running at 0.0.0.0:" + str(port))
    serve(app, host="0.0.0.0", port=port)


