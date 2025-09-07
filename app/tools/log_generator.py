import random
from datetime import datetime, timedelta
from typing import Dict, Literal, Optional
from langchain_core.tools import tool

Profile = Literal[
    "python-traceback",
    "node-unhandled-rejection",
    "java-null-pointer",
    "nginx-5xx",
    "k8s-crashloop",
    "db-connection-timeout",
]

def _ts(n: int) -> str:
    base = datetime.utcnow().replace(microsecond=0)
    return (base + timedelta(seconds=n)).strftime("%Y-%m-%d %H:%M:%S")

@tool("generate_test_logs", return_direct=False)
def generate_test_logs(profile: Profile = "python-traceback", lines: int = 200, seed: Optional[int] = None) -> Dict:
    """
    Generate realistic console logs for evaluation.

    Args:
        profile: Scenario type (python-traceback | node-unhandled-rejection | java-null-pointer | nginx-5xx | k8s-crashloop | db-connection-timeout)
        lines: Approximate number of lines
        seed: Optional RNG seed for reproducibility

    Returns:
        dict with keys: log_text, ground_truth (root_cause, severity, tags)
    """
    rnd = random.Random(seed)
    out = []
    truth = {"root_cause": None, "severity": "medium", "tags": []}

    if profile == "python-traceback":
        truth.update({"root_cause": "Unhandled Python exception (KeyError)", "severity": "high", "tags": ["exception","python"]})
        out.append(f"{_ts(0)} ERROR app: Unhandled exception in request handler")
        out.append("Traceback (most recent call last):")
        out.append("  File \"server.py\", line 87, in handle_request")
        out.append("    user = row['name']  # KeyError below")
        out.append("KeyError: 'name'")
    elif profile == "node-unhandled-rejection":
        truth.update({"root_cause": "UnhandledPromiseRejection (TypeError)", "severity": "high", "tags": ["exception","node"]})
        out += [
            f"{_ts(0)} WARN api: retry attempt=1 route=/checkout",
            f"{_ts(1)} ERROR api: TimeoutError: request to https://payments.example.com timed out",
            "    at Request._callback (request.js:42:13)",
            f"{_ts(2)} ERROR api: UnhandledPromiseRejectionWarning: TypeError: Cannot read properties of undefined (reading 'total')",
            "    at CheckoutService.calculate (service.js:101:9)",
        ]
    elif profile == "java-null-pointer":
        truth.update({"root_cause": "NullPointerException in OrderService", "severity": "critical", "tags": ["exception","java"]})
        out += [
            f"{_ts(0)} INFO OrderService - processing order id=123",
            f"{_ts(1)} ERROR OrderService - java.lang.NullPointerException: Cannot invoke \"String.length()\" because \"customerId\" is null",
            "    at com.acme.order.OrderService.validate(OrderService.java:58)",
            "    at com.acme.order.OrderService.submit(OrderService.java:112)",
        ]
    elif profile == "nginx-5xx":
        truth.update({"root_cause": "Backend 5xx spikes under load", "severity": "high", "tags": ["http","latency"]})
        for i in range(lines):
            code = rnd.choices([200, 204, 500, 502, 503], weights=[85,5,3,4,3])[0]
            ms = rnd.randint(20, 2000)
            out.append(f"{_ts(i)} INFO nginx: \"GET /api/v1/items\" {code} {ms}ms")
    elif profile == "k8s-crashloop":
        truth.update({"root_cause": "Container OOM leading to CrashLoopBackOff", "severity": "high", "tags": ["k8s","oom"]})
        out += [
            f"{_ts(0)} INFO kubelet: Created container app-7b9f...",
            f"{_ts(15)} WARN kernel: Out of memory: Killed process 1234 (app) total-vm:2048000kB",
            f"{_ts(16)} ERROR kubelet: Back-off restarting failed container app-7b9f... CrashLoopBackOff",
        ]
    elif profile == "db-connection-timeout":
        truth.update({"root_cause": "Database connection timeout / pool exhaustion", "severity": "medium", "tags": ["db","timeout"]})
        for i in range(lines):
            if i % 17 == 0:
                out.append(f"{_ts(i)} WARN db: retrying connection ...")
            if i % 29 == 0:
                out.append(f"{_ts(i)} ERROR db: timeout acquiring connection from pool (30s)")
            else:
                out.append(f"{_ts(i)} INFO app: processed request id={1000+i}")

    # pad to requested length
    while len(out) < lines:
        out.append(f"{_ts(len(out))} INFO app: heartbeat ok")

    return {"log_text": "\n".join(out), "ground_truth": truth, "profile": profile}