import time
import csv
import random
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

SERVICE2_URL = "http://service2.mesh-demo.svc.cluster.local:5001/content"

@app.route("/measure")
def measure():
    n = int(request.args.get("n", 6000))
    interval = float(request.args.get("interval", 0.5))

    latencies = []
    fail_count = 0

    session = requests.Session()
    session.keep_alive = True

    for i in range(n):
        t0 = time.perf_counter()
        try:
            r = session.get(SERVICE2_URL, timeout=2)
            r.raise_for_status()
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000)
        except:
            latencies.append(None)
            fail_count += 1

        time.sleep(interval + random.expovariate(1/0.2))

    valid = [x for x in latencies if x is not None]
    result = {
        "requests": n,
        "success": len(valid),
        "failures": fail_count,
        "avg_ms": sum(valid)/len(valid) if valid else None
    }

    with open("/app/latency_results.csv", "w") as f:
        w = csv.writer(f)
        w.writerow(["index","latency_ms"])
        for i,l in enumerate(latencies):
            w.writerow([i+1, l if l else "FAIL"])

    return jsonify(result)

@app.route("/")
def root():
    return "Service1 SDP Mode Active", 200

if __name__ == "__main__":
    app.run("0.0.0.0", 5000)
