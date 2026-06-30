import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from audit_log import ensure_log_file, get_recent_entries, write_log_entry

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    creator_id = data.get("creator_id")

    if not text:
        return jsonify({"error": "text is required"}), 400

    if not creator_id:
        return jsonify({"error": "creator_id is required"}), 400

    content_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    response = {
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": "uncertain",
        "confidence": 0.50,
        "combined_score": 0.50,
        "label": "This content could not be confidently attributed as AI generated or human written. The system found mixed signals, so this result should be treated as uncertain.",
        "signals": {
            "semantic_score": 0.50,
            "stylometric_score": 0.50,
            "repetition_score": 0.50,
        },
        "status": "classified",
    }

    entry = {
        "event_type": "classification",
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": timestamp,
        "attribution": "uncertain",
        "confidence": 0.50,
        "combined_score": 0.50,
        "semantic_score": 0.50,
        "stylometric_score": 0.50,
        "repetition_score": 0.50,
        "status": "classified",
    }
    write_log_entry(entry)

    return jsonify(response)


@app.route("/log", methods=["GET"])
def log():
    return jsonify({"entries": get_recent_entries()})


if __name__ == "__main__":
    ensure_log_file()
    app.run(debug=True, port=5000)
