"""
Vulhub target app for CVE-2018-1000656
======================================
A minimal Flask app that accepts arbitrary JSON bodies.
The vulnerable image pins Flask==0.12.2.
"""
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return "POST JSON to /json to trigger the vulnerable parser."


@app.route("/json", methods=["POST"])
def echo_json():
    data = request.get_json(force=True, silent=False)
    return jsonify({"echo": data})


if __name__ == "__main__":
    # Vulhub runs the dev server on 0.0.0.0:8000 (vulnerable config on purpose)
    app.run(host="0.0.0.0", port=8000, debug=False)
