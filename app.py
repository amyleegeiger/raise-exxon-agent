import os
import json
import asyncio
from flask import Flask, request, jsonify, render_template
from claude_note import generate_handoff_note
from agent import write_to_workllama

app = Flask(__name__)


@app.route("/")
def index():
    candidate = {
        "first_name": request.args.get("first_name", ""),
        "last_name": request.args.get("last_name", ""),
        "email": request.args.get("email", ""),
        "phone": request.args.get("phone", ""),
        "city": request.args.get("city", ""),
        "state": request.args.get("state", ""),
        "source": request.args.get("source", ""),
        "req_id": request.args.get("req_id", ""),
        "req_title": request.args.get("req_title", ""),
    }
    return render_template("screening_form.html", candidate=candidate)


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "error": "No data received"}), 400

    required = ["first_name", "last_name", "email", "req_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        handoff_note = generate_handoff_note(data)
        data["handoff_note"] = handoff_note
    except Exception as e:
        return jsonify({"success": False, "error": f"Note generation failed: {str(e)}"}), 500

    try:
        result = asyncio.run(write_to_workllama(data))
        return jsonify({"success": True, "note_preview": handoff_note, "workllama": result})
    except Exception as e:
        return jsonify({"success": False, "error": f"WorkLlama write failed: {str(e)}"}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
