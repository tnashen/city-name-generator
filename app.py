#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify
from random_city import random_city
from llm_city import generate_city_names
from job_queue import job_queue

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

VALID_CATEGORIES = ["all", "fantasy", "medieval", "sci-fi", "ancient"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/random")
def api_random():
    category = request.args.get("category", "all").lower()
    count    = int(request.args.get("count", 1))
    if category not in VALID_CATEGORIES:
        return jsonify({"error": "Invalid category"}), 400
    if not (1 <= count <= 10):
        return jsonify({"error": "Count must be 1–10"}), 400
    try:
        names = random_city(category=category, count=count)
        return jsonify({"names": names, "category": category})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data        = request.get_json() or {}
    description = data.get("description", "").strip()
    category    = data.get("category", "any").strip().lower()
    if not description:
        return jsonify({"error": "City description is required"}), 400
    job_id = job_queue.submit(generate_city_names, description, category=category, count=2)
    return jsonify({"job_id": job_id}), 202


@app.route("/api/generate/status/<job_id>")
def api_generate_status(job_id):
    result = job_queue.status(job_id)
    if result is None:
        return jsonify({"error": "Job not found or expired"}), 404
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5558, debug=False)
