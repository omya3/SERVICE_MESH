# service1/client.py
import time
import csv
import random
import requests
import threading
import queue
from statistics import mean
from flask import Flask, jsonify, request

app = Flask(__name__)

SERVICE2_URL = "http://service2.mesh-demo.svc.cluster.local:5001/content"

# ---------- existing "fixed-interval" endpoint ----------
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
        except Exception:
            latencies.append(None)
            fail_count += 1

        time.sleep(interval + random.expovariate(1/0.2))

    valid = [x for x in latencies if x is not None]
    result = {
        "requests": n,
        "success": len(valid),
        "failures": fail_count,
        "avg_ms": (sum(valid)/len(valid)) if valid else None
    }

    with open("/app/latency_results.csv", "w") as f:
        w = csv.writer(f)
        w.writerow(["index", "latency_ms", "ok"])
        for i, l in enumerate(latencies, 1):
            ok = "yes" if l is not None else "no"
            w.writerow([i, f"{l:.3f}" if l is not None else "", ok])

    return jsonify(result)

# ---------- NEW: RPS-based load endpoint ----------
class RateLimiter:
    def __init__(self, rps: float):
        self.rps = max(0.0001, rps)
        self.tokens = 0.0
        self.last = time.time()

    def wait(self):
        while True:
            now = time.time()
            self.tokens += (now - self.last) * self.rps
            self.last = now
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return
            time.sleep(0.001)

def _worker(session, url, limiter, deadline, timeout, outq):
    while time.time() < deadline:
        limiter.wait()
        t0 = time.perf_counter()
        ok = True
        try:
            r = session.get(url, timeout=timeout)
            r.raise_for_status()
        except Exception:
            ok = False
        t1 = time.perf_counter()
        outq.put((ok, (t1 - t0) * 1000.0))

@app.route("/measure_rps")
def measure_rps():
    rps        = float(request.args.get("rps", "5"))
    duration   = int(request.args.get("duration", "60"))
    concurrency= int(request.args.get("concurrency", "8"))
    timeout    = float(request.args.get("timeout", "2.0"))

    target = SERVICE2_URL
    session = requests.Session()
    session.mount("http://", requests.adapters.HTTPAdapter(
        pool_connections=concurrency, pool_maxsize=concurrency*2))

    # Warm-up (don’t count handshake)
    try:
        session.get(target, timeout=timeout)
    except Exception:
        pass

    limiter = RateLimiter(rps)
    deadline = time.time() + duration
    outq = queue.Queue()
    threads = []
    for _ in range(concurrency):
        t = threading.Thread(target=_worker,
                             args=(session, target, limiter, deadline, timeout, outq),
                             daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    # Drain results
    results = []
    while not outq.empty():
        results.append(outq.get())

    oks = [lat for ok, lat in results if ok]
    fails = len(results) - len(oks)

    # percentiles
    def pct(vals, p):
        if not vals: return None
        vals = sorted(vals)
        k = int(round((p/100.0)*(len(vals)-1)))
        return vals[max(0, min(len(vals)-1, k))]

    summary = {
        "count": len(results),
        "success": len(oks),
        "fail": fails,
        "min_ms": min(oks) if oks else None,
        "p50_ms": pct(oks, 50),
        "p90_ms": pct(oks, 90),
        "p99_ms": pct(oks, 99),
        "max_ms": max(oks) if oks else None,
        "avg_ms": mean(oks) if oks else None,
        "params": {"rps": rps, "duration": duration, "concurrency": concurrency, "timeout": timeout}
    }

    # Write CSV
    with open("/app/latency_results.csv", "w") as f:
        w = csv.writer(f)
        w.writerow(["ok", "latency_ms"])
        for ok, lat in results:
            w.writerow([1 if ok else 0, f"{lat:.3f}"])

    return jsonify(summary)

@app.route("/")
def root():
    return "Service1 (mesh) — load endpoints: /measure and /measure_rps", 200

if __name__ == "__main__":
    app.run("0.0.0.0", 5000)
