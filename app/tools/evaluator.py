import json
import re
from typing import Any, Dict, Optional
from langchain_core.tools import tool

# Optional tolerant JSON parser (handles single quotes, trailing commas, etc.)
try:  # pragma: no cover
    import json5 as _json5  # type: ignore
except Exception:  # pragma: no cover
    _json5 = None

# ------------------------
# Robust JSON coercion utils
# ------------------------

def _strip_code_fences(s: str) -> str:
    if not isinstance(s, str):
        return s
    s = s.strip()
    # Remove leading/trailing markdown code fences like ```json ... ```
    s = re.sub(r"^```[a-zA-Z0-9_-]*", "", s)
    s = re.sub(r"```$", "", s)
    return s.strip()


def _first_balanced_json_object(s: str) -> Optional[str]:
    """Extract the first balanced {...} block. Fallback for LLM text with pre/post amble."""
    start = s.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        else:
            if ch == '"':
                in_str = True
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return s[start : i + 1]
    return None


def _json_loads_tolerant(s: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(s)
    except Exception:
        pass
    if _json5 is not None:
        try:
            result = _json5.loads(s)
            if isinstance(result, dict):
                return result
        except Exception:
            pass
    return None


def _coerce_to_dict(obj: Any, label: str) -> Dict[str, Any]:
    """
    Best-effort conversion of many response shapes into a dict.
    Accepts dicts, Pydantic BaseModel, LangChain messages, or JSON-ish strings (even with code fences).
    Returns {ok: bool, value?: dict, error?: str, preview?: str}
    """
    # Native dict
    if isinstance(obj, dict):
        return {"ok": True, "value": obj}

    # Pydantic models
    try:
        if hasattr(obj, "model_dump"):
            return {"ok": True, "value": obj.model_dump()}  # type: ignore[attr-defined]
    except Exception:
        pass
    try:
        if hasattr(obj, "dict"):
            return {"ok": True, "value": obj.dict()}  # type: ignore[attr-defined]
    except Exception:
        pass

    # LangChain/AI message-like objects
    if hasattr(obj, "content") and isinstance(getattr(obj, "content"), str):
        obj = getattr(obj, "content")

    # Must be a string by now (best-effort)
    if not isinstance(obj, str):
        obj = str(obj)

    s = _strip_code_fences(obj)

    # Try direct parse
    parsed = _json_loads_tolerant(s)
    if parsed is not None:
        return {"ok": True, "value": parsed}

    # Try to extract first {...} block
    cand = _first_balanced_json_object(s)
    if cand:
        parsed = _json_loads_tolerant(cand)
        if parsed is not None:
            return {"ok": True, "value": parsed}

    # Nothing worked
    return {
        "ok": False,
        "error": f"Could not coerce {label} to JSON dict.",
        "preview": s[:500],
    }


@tool("score_report", return_direct=False)
def score_report(report_json: Any, ground_truth_json: Optional[Any] = None) -> Dict:
    """
    Robust scorer for a LogDiagnosisReport-like payload.

    Input can be a dict, a Pydantic model, a LangChain message, or a JSON string
    (even if wrapped in markdown fences or containing extra text). The function
    normalizes inputs and returns a simple accuracy dict useful for synthetic evals.

    Returns:
        {
          ok: bool,
          score: int,                # higher is better
          checks: list,              # which checks passed
          normalized_report: dict,   # the parsed report (when ok)
          normalized_truth: dict|None
        }
    """
    rep = _coerce_to_dict(report_json, "report_json")
    if not rep["ok"]:
        return {"ok": False, "error": rep.get("error"), "preview": rep.get("preview")}

    gt_dict = None
    if ground_truth_json is not None:
        gt = _coerce_to_dict(ground_truth_json, "ground_truth_json")
        if gt["ok"]:
            gt_dict = gt["value"]
        else:
            # Non-fatal; we still score what we can
            gt_dict = None

    report = rep["value"]

    # Pull common fields defensively
    summary = str(report.get("summary") or "").strip()
    suspected_causes = report.get("suspected_causes") or []
    if not isinstance(suspected_causes, list):
        suspected_causes = [str(suspected_causes)]

    next_actions = report.get("next_actions") or []
    if not isinstance(next_actions, list):
        next_actions = [str(next_actions)]

    haystack = (summary + " " + " ".join(map(str, suspected_causes))).lower()

    score = 0
    checks = []

    # 1) Root cause mentioned
    if gt_dict and gt_dict.get("root_cause"):
        root = str(gt_dict["root_cause"]).lower()
        # token-overlap heuristic
        root_tokens = [t for t in re.split(r"[^a-z0-9_]+", root) if t]
        rc_hit = any(t in haystack for t in root_tokens)
        score += 1 if rc_hit else 0
        checks.append({"check": "root_cause_mentioned", "pass": rc_hit, "tokens": root_tokens[:6]})

    # 2) Tag overlap
    if gt_dict and isinstance(gt_dict.get("tags"), list):
        tags = [str(t).lower() for t in gt_dict["tags"]]
        tag_hits = sum(1 for t in tags if t in haystack)
        score += min(tag_hits, 3)  # cap to avoid runaway scores
        checks.append({"check": "tag_overlap", "hits": tag_hits, "tags": tags[:6]})

    # 3) Has next actions
    has_actions = any(str(a).strip() for a in next_actions)
    score += 1 if has_actions else 0
    checks.append({"check": "has_next_actions", "pass": has_actions})

    return {
        "ok": True,
        "score": score,
        "checks": checks,
        "normalized_report": report,
        "normalized_truth": gt_dict,
    }
