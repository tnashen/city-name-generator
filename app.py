#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify, Response
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


@app.route("/robots.txt")
def robots():
    return Response("User-agent: *\nAllow: /\nSitemap: http://10.10.10.108:5558/sitemap.xml\n",
                    mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    xml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           '<url><loc>http://10.10.10.108:5558/</loc><changefreq>monthly</changefreq><priority>1.0</priority></url>'
           '</urlset>')
    return Response(xml, mimetype="application/xml")

@app.route("/llms.txt")
def llms_txt():
    content = """# City Name Generator

> A free tool to generate city and town names for fantasy, medieval, sci-fi, and ancient settings.

## What this site does

City Name Generator provides two modes:
- **Random mode**: draws from 2,000+ curated city names across four styles
- **AI mode**: generates 2 unique city names from a user-provided description, with lore notes

## Who it's for

Writers, game designers, tabletop RPG players (D&D, Pathfinder), video game developers, and world builders creating fictional settings.

## Name styles

- **Fantasy**: Elvish, arcane, and epic-sounding names for magical worlds
- **Medieval**: Anglo-Saxon, Germanic, and Latin-root names for historical or low-fantasy settings
- **Sci-Fi**: Technical, hybrid names with Greek/Latin roots for space colonies, megacities, and stations
- **Ancient**: Sumerian, Egyptian, Greek, and Roman-inspired names for ancient civilizations

## Technology

Flask web app. AI names via Featherless AI (Qwen 2.5). No login required. Free to use.
"""
    return Response(content, mimetype="text/plain")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5558, debug=False)
