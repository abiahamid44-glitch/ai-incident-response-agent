# AI Incident Response & Workflow Automation Agent

A portfolio-ready agentic AI project that analyzes software incidents, classifies them, routes them through a multi-step workflow, and produces a structured remediation report.

## Why this project

This project combines:
- **Python**
- **LangGraph**
- **Hugging Face Inference**
- **FastAPI**
- **Structured LLM output**
- **Agentic workflow orchestration**
- **Incident/log analysis**
- **Automated remediation recommendations**

It is designed to demonstrate practical backend + AI engineering skills rather than just calling an LLM once.

## What the agent does

Given an incident such as:

> `API requests are timing out after deployment. Logs show repeated connection pool exhaustion errors.`

the workflow:

1. **Normalizes the incident**
2. **Classifies the issue**
3. **Assesses severity**
4. **Chooses an analysis path**
5. **Generates troubleshooting steps**
6. **Creates a structured incident report**
7. **Returns the result through a FastAPI endpoint**

## Architecture

```text
Incoming Incident
       |
       v
Normalize Input
       |
       v
Classify Incident
       |
       v
Assess Severity
       |
       v
Route by Category
   /      |       \
network  app     database
   \      |       /
       v
Generate Resolution Plan
       |
       v
Create Final Report
```

## Project structure

```text
ai_incident_response_agent/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── llm.py
│   ├── models.py
│   ├── workflow.py
│   └── main.py
├── data/
│   └── sample_incidents.json
├── tests/
│   └── test_workflow.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your environment file

Copy:

```bash
cp .env.example .env
```

Then add your Hugging Face token:

```env
HUGGINGFACE_API_TOKEN=your_token_here
HF_MODEL=Qwen/Qwen2.5-7B-Instruct
```

You can create a Hugging Face access token from your account settings.

## Run the API

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

Use the `/analyze` endpoint and submit:

```json
{
  "title": "Database connection failures",
  "description": "After deployment, API requests began failing. Logs show too many database connections and timeout errors.",
  "source": "production-api"
}
```

## Run without an API key

The project includes a deterministic fallback mode so the workflow can still be demonstrated and tested without sending requests to Hugging Face.

If no `HUGGINGFACE_API_TOKEN` is present, the app will use rule-based classification and remediation templates.

That makes the project easy for recruiters to clone and test.

## Run tests

```bash
pytest
```

## Example output

```json
{
  "category": "database",
  "severity": "high",
  "summary": "The service is likely exhausting available database connections.",
  "probable_causes": [
    "Connection pool is undersized",
    "Connections are not being released",
    "Traffic increased after deployment"
  ],
  "recommended_actions": [
    "Inspect active and idle database connections",
    "Verify connection pool limits",
    "Check application connection lifecycle",
    "Review deployment changes",
    "Monitor error rate after remediation"
  ],
  "status": "analysis_complete"
}
```

## Future improvements

- Connect to real log files
- Add vector search over runbooks
- Add a Jira/ServiceNow ticket creation tool
- Add observability with LangSmith or OpenTelemetry
- Add retrieval-augmented generation over internal troubleshooting documentation
- Add confidence scores and human approval before remediation
