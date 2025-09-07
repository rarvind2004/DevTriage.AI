import json
from typing import Dict, Optional
from langchain_core.tools import tool

@tool("score_report", return_direct=False)
def score_report(report_json: str, ground_truth_json: Optional[str] = None) -> Dict:
    """
    Heuristic scorer for a LogDiagnosisReport (JSON string). If ground_truth provided (JSON),
    checks keyword overlap with expected root cause and tags.
    Returns a simple accuracy dict useful for A/B checks on generated logs.
    """
    try:
        report = json.loads(report_json)
    except Exception:
        return {"ok": False, "error": "report_json not valid JSON"}

    gt = None
    if ground_truth_json:
        try:
            gt = json.loads(ground_truth_json)
        except Exception:
            gt = None

    summary = (report.get("summary") or "") + " " + " ".join(report.get("suspected_causes", []))
    score = 0
    checks = []

    if gt and gt.get("root_cause"):
        root = gt["root_cause"].lower()
        hit = any(tok in summary.lower() for tok in root.split())
        score += 1 if hit else 0
        checks.append({"check": "root_cause_mentioned", "pass": hit})

    if gt and gt.get("tags"):
        tag_hits = sum(1 for t in gt["tags"] if t.lower() in summary.lower())
        score += tag_hits
        checks.append({"check": "tag_overlap", "hits": tag_hits})

    has_actions = bool(report.get("next_actions"))
    score += 1 if has_actions else 0
    checks.append({"check": "has_next_actions", "pass": has_actions})

    return {"ok": True, "score": score, "checks": checks}