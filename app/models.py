from typing import Literal
from pydantic import BaseModel, Field


IncidentCategory = Literal[
    "network",
    "application",
    "database",
    "authentication",
    "performance",
    "unknown",
]

Severity = Literal["low", "medium", "high", "critical"]


class IncidentRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    source: str = Field(default="unknown")


class IncidentReport(BaseModel):
    category: IncidentCategory
    severity: Severity
    summary: str
    probable_causes: list[str]
    recommended_actions: list[str]
    status: str = "analysis_complete"
