from pydantic import BaseModel, Field
from typing import List, Optional

class TriageResult(BaseModel):
    symptoms: str = Field(description="Summary of the symptoms.")
    expected_behavior: str = Field(description="What should be happening instead? ")
    actual_behavior: str = Field(description="What is actually occurring? ")
    environment: str = Field(description="System environment.")
    prioritized_hypotheses: List[str] = Field(description="List of initial theories.")

class LogAnalysisResult(BaseModel):
    error_signature: str = Field(description="The primary error trace or code.")
    key_anomalies: List[str] = Field(description="List of anomalies spotted in logs.")
    correlation: str = Field(description="Correlation of error to operations or versions.")

class ReproductionResult(BaseModel):
    repro_script_path: str = Field(description="Path to the created repro script.")
    run_command: str = Field(description="Command used to run the test.")
    outcome: str = Field(description="Output that demonstrates the crash.")
    is_minimal: bool = Field(description="Is this a minimal reproducible example?")

class FixPlanResult(BaseModel):
    root_cause_hypothesis: str = Field(description="The suspected root cause.")
    patch_approach: str = Field(description="How to fix the issue.")
    impacted_files: List[str] = Field(description="Files to be edited to patch the issue.")
    confidence: str = Field(description="Confidence level (e.g., HIGH, MEDIUM, LOW)")
    verification_plan: str = Field(description="Tests to add, regression checks.")

class ReviewResult(BaseModel):
    approved: bool = Field(description="Is the plan safe and complete?")
    reviewer_comments: str = Field(description="Comments and critiques.")
    edge_cases: List[str] = Field(description="Any edge cases to consider.")

class FinalReport(BaseModel):
    bug_summary: dict
    evidence: dict
    reproduction: dict
    root_cause: str
    confidence: str
    patch_plan: dict
    validation_plan: str
    open_questions: List[str]
