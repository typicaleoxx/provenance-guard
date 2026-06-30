import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request

from audit_log import ensure_log_file, get_recent_entries, write_log_entry
from detector import (
    get_repetition_score,
    get_semantic_score,
    get_stylometric_score,
)
from scoring import combine_scores, get_attribution, get_confidence

app = Flask(__name__)

LABELS = {
    "likely_ai": "This content shows strong signs of being AI generated. The system found consistent patterns across multiple detection signals. A creator may appeal this label if they believe it is incorrect.",
    "likely_human": "This content shows strong signs of being human written. The system found natural variation across multiple detection signals, but this label is not a guarantee of authorship.",
    "uncertain": "This content could not be confidently attributed as AI generated or human written. The system found mixed signals, so this result should be treated as uncertain.",
}


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

    semantic_score = get_semantic_score(text)
    stylometric_score = get_stylometric_score(text)
    repetition_score = get_repetition_score(text)

    combined_score = combine_scores(
        semantic_score, stylometric_score, repetition_score
    )
    attribution = get_attribution(combined_score)
    confidence = get_confidence(combined_score, attribution)

    response = {
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": attribution,
        "confidence": confidence,
        "combined_score": combined_score,
        "label": LABELS[attribution],
        "signals": {
            "semantic_score": semantic_score,
            "stylometric_score": stylometric_score,
            "repetition_score": repetition_score,
        },
        "status": "classified",
    }

    entry = {
        "event_type": "classification",
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": timestamp,
        "attribution": attribution,
        "confidence": confidence,
        "combined_score": combined_score,
        "semantic_score": semantic_score,
        "stylometric_score": stylometric_score,
        "repetition_score": repetition_score,
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
