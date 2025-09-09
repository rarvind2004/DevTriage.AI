import json
from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

# -----------------------------
# Pydantic Schemas
# -----------------------------

class NormalizedReport(BaseModel):
    summary: str
    severity: Literal["critical", "high", "medium", "low"]
    suspected_causes: List[str]
    evidence: List[str]
    impacted_components: List[str]
    repro_steps: List[str]
    experiments: List[str]
    next_actions: List[str]
    owner_suggestions: List[str]
    notes: Optional[str] = None

class CriterionGrade(BaseModel):
    name: Literal["relevance", "clarity", "completeness", "accuracy", "actionability"]
    score: int = Field(ge=1, le=5)
    rationale: str

class GradeResult(BaseModel):
    ok: bool
    overall_score: int = Field(description="Sum of criterion scores (max 25)")
    grade: Literal["A", "B", "C", "D", "F"]
    decision: Literal["pass", "needs_improvement"]
    criteria: List[CriterionGrade]
    groundedness: Literal["high", "medium", "low"]
    extracted_facts: List[str] = []
    missing_elements: List[str] = []
    normalized_report: Optional[NormalizedReport] = None
    notes: Optional[str] = None

# -----------------------------
# Helpers
# -----------------------------

def _get_model() -> ChatGoogleGenerativeAI:
    # Uses GOOGLE_API_KEY from environment
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2)

def _safe_json_loads(maybe_json: str) -> Optional[dict]:
    try:
        return json.loads(maybe_json)
    except Exception:
        return None

def _normalize_report_via_ai(report_input: Union[str, dict]) -> NormalizedReport:
    """Robustly coerce an arbitrary report (dict or text) into NormalizedReport using the LLM.
    Falls back to a best-effort minimal structure if the model is unavailable.
    """
    if isinstance(report_input, dict):
        # Try direct model validation first
        try:
            return NormalizedReport(**report_input)
        except Exception:
            pass

    # If it's a string, try JSON first
    if isinstance(report_input, str):
        obj = _safe_json_loads(report_input)
        if obj is not None:
            try:
                return NormalizedReport(**obj)
            except Exception:
                # will attempt AI normalization below
                pass
        raw_text = report_input
    else:
        raw_text = json.dumps(report_input)

    # AI normalization to schema
    try:
        model = _get_model().with_structured_output(NormalizedReport)
        prompt = (
            "Normalize the following debugging report to the schema. "
            "Extract concrete content. If a field is missing, infer conservatively from context.\n\n"
            f"REPORT:\n{raw_text}"
        )
        raw_result = model.invoke(prompt)
        if isinstance(raw_result, NormalizedReport):
            return raw_result
        elif isinstance(raw_result, dict):
            return NormalizedReport(**raw_result)
        elif isinstance(raw_result, BaseModel):
            return NormalizedReport(**raw_result.model_dump())
        else:
            raise ValueError("Unexpected result type from model.invoke")
    except Exception:
        # Minimal fallback to keep tool resilient
        return NormalizedReport(
            summary="Unparsed report; minimal fallback.",
            severity="medium",
            suspected_causes=[],
            evidence=[],
            impacted_components=[],
            repro_steps=[],
            experiments=[],
            next_actions=[],
            owner_suggestions=[],
            notes=None,
        )

def _ai_grade(report: NormalizedReport, log_text: Optional[str], ground_truth: Optional[dict], rubric: Optional[str]) -> GradeResult:
    rubric_text = rubric or (
        "Grade the response against these criteria (1-5 each):\n"
        "- relevance: Does it directly address the provided logs and user ask?\n"
        "- clarity: Is it easy to follow with specific references?\n"
        "- completeness: Does it cover root cause, evidence, and next steps?\n"
        "- accuracy: Are claims consistent with the log evidence and any ground truth?\n"
        "- actionability: Are next actions prioritized and concrete?\n"
        "Return a balanced assessment; avoid inflating scores."
    )

    # Build grading context
    gt_str = json.dumps(ground_truth) if ground_truth else "{}"

    try:
        model = _get_model().with_structured_output(GradeResult)
        prompt = (
            "You are an evaluation subagent. Read LOGS and a candidate RESPONSE. "
            "Use the RUBRIC to grade. Cite concrete evidence from the logs when judging accuracy.\n\n"
            f"RUBRIC:\n{rubric_text}\n\n"
            f"LOGS:\n{(log_text or '<<no logs provided>>')}\n\n"
            f"GROUND_TRUTH (optional):\n{gt_str}\n\n"
            f"RESPONSE (normalized JSON):\n{report.model_dump_json() }\n\n"
            "Output a GradeResult JSON."
        )
        raw_result = model.invoke(prompt)
        if isinstance(raw_result, GradeResult):
            graded = raw_result
        elif isinstance(raw_result, dict):
            graded = GradeResult(**raw_result)
        elif isinstance(raw_result, BaseModel):
            graded = GradeResult(**raw_result.model_dump())
        else:
            raise ValueError("Unexpected result type from model.invoke")
        # Attach the normalized report for traceability
        graded.normalized_report = report
        return graded
    except Exception as e:
        # Fallback lightweight heuristic if the LLM call fails
        summary = f"{report.summary} {' '.join(report.suspected_causes)}".lower()
        # very simple scores
        rel = 3 if summary else 1
        cla = 3 if len(report.next_actions) or len(report.evidence) else 2
        com = 3 if all([report.repro_steps, report.next_actions]) else 2
        acc = 3
        act = 3 if report.next_actions else 2
        total = rel + cla + com + acc + act
        grade = "A" if total >= 23 else "B" if total >= 19 else "C" if total >= 15 else "D" if total >= 12 else "F"
        decision = "pass" if total >= 18 else "needs_improvement"
        return GradeResult(
            ok=False,
            overall_score=total,
            grade=grade,
            decision=decision,
            criteria=[
                CriterionGrade(name="relevance", score=rel, rationale="Fallback heuristic"),
                CriterionGrade(name="clarity", score=cla, rationale="Fallback heuristic"),
                CriterionGrade(name="completeness", score=com, rationale="Fallback heuristic"),
                CriterionGrade(name="accuracy", score=acc, rationale="Fallback heuristic"),
                CriterionGrade(name="actionability", score=act, rationale="Fallback heuristic"),
            ],
            groundedness="medium",
            extracted_facts=[],
            missing_elements=[],
            normalized_report=report,
            notes=f"LLM grading unavailable: {type(e).__name__}",
        )

@tool("score_report", return_direct=False)
def score_report(
    report_input: Union[str, dict],
    log_text: Optional[str] = None,
    ground_truth_json: Optional[str] = None,
    rubric: Optional[str] = None,
) -> Dict:
    """
    AI-driven evaluator for a LogDiagnosisReport. Accepts either a raw text or JSON report.

    Args:
        report_input: The candidate report (string JSON, dict, or free text). The function will normalize it.
        log_text: Optional raw logs used to produce the report; improves accuracy grading.
        ground_truth_json: Optional JSON string with keys like {"root_cause": str, "tags": [..]} from synthetic generator.
        rubric: Optional custom rubric text to override the default criteria.

    Returns:
        dict: GradeResult serialized to dict, including the normalized report.
    """
    # Parse ground truth if present
    gt = _safe_json_loads(ground_truth_json) if ground_truth_json else None

    # Normalize the report to a stable schema using the AI subagent
    normalized = _normalize_report_via_ai(report_input)

    # Grade with the AI subagent (falls back to heuristic on failure)
    result = _ai_grade(normalized, log_text=log_text, ground_truth=gt, rubric=rubric)

    return result.model_dump()