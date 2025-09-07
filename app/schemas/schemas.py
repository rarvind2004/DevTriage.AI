from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class LogDiagnosisReport(BaseModel):
    summary: str = Field(description="Human-friendly overview of the incident and likely root cause(s)")
    severity: Literal["critical", "high", "medium", "low"] = Field(description="Impact level inferred from logs")
    suspected_causes: List[str] = Field(description="Short list of plausible causes")
    evidence: List[str] = Field(description="Salient log lines, stack traces, timing, counters")
    impacted_components: List[str] = Field(description="Services, endpoints, modules affected")
    repro_steps: List[str] = Field(description="Steps to reliably reproduce the issue")
    experiments: List[str] = Field(description="Targeted tests, toggles, or telemetry to validate hypotheses")
    next_actions: List[str] = Field(description="Actionable steps to mitigate or resolve the issue")
    owner_suggestions: List[str] = Field(description="Teams/roles likely responsible or best suited to fix")
    notes: Optional[str] = Field(default=None, description="Extra context or caveats")