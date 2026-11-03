import os
import socket
from flask import Flask, jsonify

app = Flask(__name__)
ready = True


@app.get("/")
def inventory():
    return jsonify(
        service="inventory",
        pod=os.getenv("HOSTNAME", socket.gethostname()),
        item="keyboard",
        quantity=25,
    )


@app.get("/health")
def health():
    return jsonify(status="alive"), 200


@app.get("/ready")
def readiness():
    if ready:
        return jsonify(status="ready"), 200
    return jsonify(status="not-ready"), 503


@app.post("/admin/fail-readiness")
def fail_readiness():
    global ready
    ready = False
    return jsonify(status="not-ready"), 200


@app.post("/admin/restore-readiness")
def restore_readiness():
    global ready
    ready = True
    return jsonify(status="ready"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
