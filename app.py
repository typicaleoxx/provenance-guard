import uuid
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from audit_log import (
    ensure_log_file,
    find_classification_by_content_id,
    get_recent_entries,
    update_classification_status,
    write_log_entry,
)
from detector import (
    get_repetition_score,
    get_semantic_score,
    get_stylometric_score,
)
from labels import get_transparency_label
from scoring import combine_scores, get_attribution, get_confidence

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
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
    label = get_transparency_label(attribution)

    response = {
        "content_id": content_id,
        "creator_id": creator_id,
        "attribution": attribution,
        "confidence": confidence,
        "combined_score": combined_score,
        "label": label,
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


@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json(silent=True) or {}
    content_id = data.get("content_id")
    creator_reasoning = data.get("creator_reasoning")

    if not content_id:
        return jsonify({"error": "content_id is required"}), 400

    if not creator_reasoning:
        return jsonify({"error": "creator_reasoning is required"}), 400

    original = find_classification_by_content_id(content_id)
    if original is None:
        return jsonify({"error": "content_id not found"}), 404

    update_classification_status(content_id, "under_review")

    entry = {
        "event_type": "appeal",
        "content_id": content_id,
        "creator_id": original.get("creator_id"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "under_review",
        "appeal_reasoning": creator_reasoning,
        "original_attribution": original.get("attribution"),
        "original_confidence": original.get("confidence"),
        "original_combined_score": original.get("combined_score"),
        "semantic_score": original.get("semantic_score"),
        "stylometric_score": original.get("stylometric_score"),
        "repetition_score": original.get("repetition_score"),
    }
    write_log_entry(entry)

    return jsonify({
        "content_id": content_id,
        "status": "under_review",
        "message": "Appeal received and marked for review.",
    })


@app.route("/log", methods=["GET"])
def log():
    return jsonify({"entries": get_recent_entries()})


if __name__ == "__main__":
    ensure_log_file()
    app.run(debug=True, port=5000)
