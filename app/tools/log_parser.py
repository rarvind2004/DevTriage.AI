import re
from typing import Dict, List, Optional
from langchain_core.tools import tool

# Basic patterns for timestamps and levels
TS = r"(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:,\d{3})?)"
LVL = r"(?P<lvl>TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)"
PY_TRACE_START = re.compile(r"Traceback \(most recent call last\):")
JS_STACK_LINE = re.compile(r"\s*at\s+.*\((.*):(\d+):(\d+)\)")
JAVA_EXC = re.compile(r"([A-Za-z0-9_$.]+Exception|Error):\s+(.*)")
HTTP_LAT = re.compile(r"\b(\d{3})\s+(\d+ms|\d+\.\d+s)\b")
TIMEOUT = re.compile(r"timeout|timed out|deadline exceeded", re.I)
OOM = re.compile(r"OutOfMemory|Killed process .* due to out of memory|OOM", re.I)
RETRY = re.compile(r"retry|retries|attempt", re.I)

@tool("parse_logs", return_direct=False)
def parse_logs(log_text: str, filename: Optional[str] = None) -> Dict:
    """
    Parse raw log text into basic structure and extract signals.

    Args:
    log_text: Full text of logs (paste or read from file externally)
    filename: Optional file hint (used only for metadata)

    Returns:
    dict with keys: events, errors, exceptions, stack_traces, counts, signals
    """
    lines = log_text.splitlines()
    events: List[Dict] = []
    errors: List[str] = []
    exceptions: List[str] = []
    stacks: List[str] = []
    counts = {"ERROR": 0, "WARN": 0, "INFO": 0, "DEBUG": 0}
    signals = set()


    for ln in lines:
        # level detection
        lvl_match = re.search(LVL, ln)
        lvl = lvl_match.group("lvl") if lvl_match else None
        if lvl in counts:
            counts[lvl] += 1
        # timestamp
        ts_match = re.search(TS, ln)
        ts = ts_match.group("ts") if ts_match else None
        # exceptions
        m_java = JAVA_EXC.search(ln)
        if m_java:
            exceptions.append(f"{m_java.group(1)}: {m_java.group(2)}")
            errors.append(ln)
        if "Exception" in ln or "Error:" in ln or "ERROR" in ln:
            errors.append(ln)
        if PY_TRACE_START.search(ln) or JS_STACK_LINE.search(ln):
            stacks.append(ln)
        if TIMEOUT.search(ln):
            signals.add("timeout")
        if OOM.search(ln):
            signals.add("oom")
        if RETRY.search(ln):
            signals.add("retries")
        if HTTP_LAT.search(ln):
            signals.add("http_latency")
        events.append({"ts": ts, "lvl": lvl, "line": ln})

    suspected = []
    if "oom" in signals:
        suspected.append("Memory exhaustion / leak")
    if "timeout" in signals:
        suspected.append("Network or downstream timeout / slow dependency")
    if counts["ERROR"] > 0 and "http_latency" in signals:
        suspected.append("HTTP 5xx or slow responses under error burst")
    if exceptions:
        suspected.append("Unhandled exception / missing error handling")

    return {
        "filename": filename,
        "events": events[:1000], # cap to keep payload manageable
        "errors": errors[:200],
        "exceptions": exceptions[:100],
        "stack_traces": stacks[:200],
        "counts": counts,
        "signals": sorted(list(signals)),
        "suspected": suspected,
        "total_lines": len(lines),
    }