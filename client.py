import time
import csv
import random
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

SERVICE2_URL = "http://service2.mesh-demo.svc.cluster.local:5001/content"

@app.route("/measure")
def measure():
    """Perform SDP-style latency measurement."""
    n = int(request.args.get("n", 6000))          # number of requests
    interval = float(request.args.get("interval", 0.5))  # ~0.5 sec per request (≈2 RPS)

    latencies = []
    fail_count = 0

    session = requests.Session()   # reuse TCP connection (same as SDP)
    session.keep_alive = True

    for i in range(n):
        t0 = time.perf_counter()
        try:
            r = session.get(SERVICE2_URL, timeout=2)
            r.raise_for_status()
            t1 = time.perf_counter()
            lat_ms = (t1 - t0) * 1000
            latencies.append(lat_ms)
        except Exception:
            latencies.append(None)
            fail_count += 1

        # SDP-like traffic interval
        time.sleep(interval + random.expovariate(1/0.2))

    valid = [x for x in latencies if x is not None]
    if valid:
        avg = sum(valid) / len(valid)
        result = {
            "requests": len(latencies),
            "success": len(valid),
            "failures": fail_count,
            "min_ms": min(valid),
            "max_ms": max(valid),
            "avg_ms": avg,
        }
    else:
        result = {"error": "No successful requests"}

    # Write CSV like SDP
    with open("/app/latency_results.csv", "w") as f:
        w = csv.writer(f)
        w.writerow(["index", "latency_ms"])
        for idx, lat in enumerate(latencies):
            w.writerow([idx + 1, lat if lat else "FAIL"])

    return jsonify(result)

@app.route("/")
def root():
    return "Service1 SDP Mode Active", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
