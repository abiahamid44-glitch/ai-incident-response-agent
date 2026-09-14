from fastapi import FastAPI

from app.models import IncidentRequest, IncidentReport
from app.workflow import analyze_incident


app = FastAPI(
    title="AI Incident Response & Workflow Automation Agent",
    version="1.0.0",
    description=(
        "Agentic workflow that classifies software incidents, assesses severity, "
        "routes analysis, and generates remediation recommendations."
    ),
)


@app.get("/")
def root():
    return {
        "name": "AI Incident Response & Workflow Automation Agent",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze", response_model=IncidentReport)
def analyze(request: IncidentRequest) -> IncidentReport:
    return analyze_incident(
        title=request.title,
        description=request.description,
        source=request.source,
    )
