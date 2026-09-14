from __future__ import annotations

from typing import TypedDict, Literal

from langgraph.graph import StateGraph, START, END

from app.llm import llm
from app.models import IncidentReport


class IncidentState(TypedDict, total=False):
    title: str
    description: str
    source: str

    normalized_text: str
    category: str
    severity: str
    summary: str
    probable_causes: list[str]
    recommended_actions: list[str]
    status: str


CATEGORY_KEYWORDS = {
    "network": [
        "dns", "socket", "tcp", "connection refused", "packet", "network",
        "host unreachable", "latency", "firewall",
    ],
    "database": [
        "database", "sql", "sqlite", "postgres", "mysql", "connection pool",
        "deadlock", "query", "db connection",
    ],
    "authentication": [
        "auth", "authentication", "login", "token", "jwt", "permission",
        "unauthorized", "forbidden", "credential",
    ],
    "performance": [
        "slow", "latency", "timeout", "cpu", "memory", "performance",
        "throughput", "overload",
    ],
    "application": [
        "exception", "traceback", "null", "crash", "500", "bug", "deployment",
        "application", "service",
    ],
}


def normalize_input(state: IncidentState) -> IncidentState:
    title = state["title"].strip()
    description = " ".join(state["description"].split())
    source = state.get("source", "unknown").strip() or "unknown"

    return {
        "normalized_text": f"{title}\n{description}",
        "source": source,
    }


def _rule_based_category(text: str) -> str:
    lowered = text.lower()
    scores: dict[str, int] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for keyword in keywords if keyword in lowered)

    best_category = max(scores, key=scores.get)

    if scores[best_category] == 0:
        return "unknown"

    return best_category


def classify_incident(state: IncidentState) -> IncidentState:
    text = state["normalized_text"]

    if llm.enabled:
        try:
            result = llm.json_response(
                system_prompt=(
                    "You classify software incidents. Return JSON only with keys "
                    '"category" and "summary". category must be one of: '
                    "network, application, database, authentication, performance, unknown."
                ),
                user_prompt=text,
            )

            category = result.get("category", "unknown")
            if category not in CATEGORY_KEYWORDS and category != "unknown":
                category = "unknown"

            summary = str(result.get("summary", "")).strip()
            if not summary:
                summary = "Software incident requires further investigation."

            return {"category": category, "summary": summary}
        except Exception:
            pass

    category = _rule_based_category(text)
    summary = _fallback_summary(category)

    return {"category": category, "summary": summary}


def assess_severity(state: IncidentState) -> IncidentState:
    text = state["normalized_text"].lower()

    critical_signals = [
        "production down",
        "complete outage",
        "data loss",
        "security breach",
        "all users",
    ]

    high_signals = [
        "production",
        "repeated",
        "timeout",
        "failing",
        "unavailable",
        "500",
    ]

    if any(signal in text for signal in critical_signals):
        severity = "critical"
    elif any(signal in text for signal in high_signals):
        severity = "high"
    elif "slow" in text or "intermittent" in text:
        severity = "medium"
    else:
        severity = "low"

    return {"severity": severity}


def route_category(
    state: IncidentState,
) -> Literal[
    "network_analysis",
    "database_analysis",
    "auth_analysis",
    "performance_analysis",
    "application_analysis",
]:
    category = state.get("category", "unknown")

    routes = {
        "network": "network_analysis",
        "database": "database_analysis",
        "authentication": "auth_analysis",
        "performance": "performance_analysis",
        "application": "application_analysis",
        "unknown": "application_analysis",
    }

    return routes.get(category, "application_analysis")


def network_analysis(state: IncidentState) -> IncidentState:
    return {
        "probable_causes": [
            "DNS or service discovery failure",
            "Firewall or routing misconfiguration",
            "Socket or upstream connectivity failure",
        ],
        "recommended_actions": [
            "Verify DNS resolution and target host availability",
            "Test connectivity to the affected service and port",
            "Inspect firewall, routing, and security-group rules",
            "Review recent infrastructure or networking changes",
            "Monitor connection errors after remediation",
        ],
    }


def database_analysis(state: IncidentState) -> IncidentState:
    return {
        "probable_causes": [
            "Database connection pool exhaustion",
            "Slow or blocked queries",
            "Connections not being released correctly",
        ],
        "recommended_actions": [
            "Inspect active, idle, and waiting database connections",
            "Review connection pool limits and application pool configuration",
            "Identify slow, blocked, or long-running queries",
            "Check whether connections are closed or returned to the pool",
            "Compare database behavior before and after recent deployments",
        ],
    }


def auth_analysis(state: IncidentState) -> IncidentState:
    return {
        "probable_causes": [
            "Expired or invalid authentication token",
            "Incorrect permissions or authorization policy",
            "Credential or identity-provider configuration issue",
        ],
        "recommended_actions": [
            "Validate token expiration, issuer, and audience",
            "Review authorization policies and role mappings",
            "Confirm configured secrets and credentials are current",
            "Inspect authentication-service logs",
            "Retry with a known-good test identity",
        ],
    }


def performance_analysis(state: IncidentState) -> IncidentState:
    return {
        "probable_causes": [
            "CPU or memory pressure",
            "Slow dependency or downstream service",
            "Traffic spike or resource saturation",
        ],
        "recommended_actions": [
            "Inspect CPU, memory, latency, and throughput metrics",
            "Identify slow dependencies and downstream calls",
            "Compare traffic volume to normal baseline",
            "Review timeouts, retries, and concurrency limits",
            "Measure performance again after mitigation",
        ],
    }


def application_analysis(state: IncidentState) -> IncidentState:
    return {
        "probable_causes": [
            "Recent application code or deployment regression",
            "Unhandled exception or invalid application state",
            "Dependency or configuration mismatch",
        ],
        "recommended_actions": [
            "Review recent deployments and code changes",
            "Inspect stack traces and application logs",
            "Reproduce the failure with the smallest possible test case",
            "Validate runtime configuration and dependency versions",
            "Roll back or patch the suspected change if appropriate",
        ],
    }


def generate_final_report(state: IncidentState) -> IncidentState:
    if llm.enabled:
        try:
            result = llm.json_response(
                system_prompt=(
                    "You are an incident-response assistant. Return JSON only with keys "
                    '"summary", "probable_causes", and "recommended_actions". '
                    "Do not invent facts. Keep recommendations concrete and safe."
                ),
                user_prompt=(
                    f"Incident:\n{state['normalized_text']}\n\n"
                    f"Category: {state['category']}\n"
                    f"Severity: {state['severity']}\n"
                    f"Current probable causes: {state['probable_causes']}\n"
                    f"Current recommended actions: {state['recommended_actions']}\n"
                ),
            )

            causes = result.get("probable_causes", state["probable_causes"])
            actions = result.get("recommended_actions", state["recommended_actions"])
            summary = result.get("summary", state["summary"])

            if isinstance(causes, list) and isinstance(actions, list):
                return {
                    "summary": str(summary),
                    "probable_causes": [str(x) for x in causes][:5],
                    "recommended_actions": [str(x) for x in actions][:7],
                    "status": "analysis_complete",
                }
        except Exception:
            pass

    return {"status": "analysis_complete"}


def _fallback_summary(category: str) -> str:
    summaries = {
        "network": "The incident appears to involve network connectivity or service communication.",
        "database": "The incident appears to involve database connectivity, query execution, or connection management.",
        "authentication": "The incident appears to involve authentication or authorization.",
        "performance": "The incident appears to involve degraded performance or resource saturation.",
        "application": "The incident appears to involve application behavior, deployment, or runtime errors.",
        "unknown": "The incident could not be confidently classified and requires broader application-level investigation.",
    }
    return summaries[category]


def build_workflow():
    graph = StateGraph(IncidentState)

    graph.add_node("normalize_input", normalize_input)
    graph.add_node("classify_incident", classify_incident)
    graph.add_node("assess_severity", assess_severity)

    graph.add_node("network_analysis", network_analysis)
    graph.add_node("database_analysis", database_analysis)
    graph.add_node("auth_analysis", auth_analysis)
    graph.add_node("performance_analysis", performance_analysis)
    graph.add_node("application_analysis", application_analysis)

    graph.add_node("generate_final_report", generate_final_report)

    graph.add_edge(START, "normalize_input")
    graph.add_edge("normalize_input", "classify_incident")
    graph.add_edge("classify_incident", "assess_severity")

    graph.add_conditional_edges(
        "assess_severity",
        route_category,
        {
            "network_analysis": "network_analysis",
            "database_analysis": "database_analysis",
            "auth_analysis": "auth_analysis",
            "performance_analysis": "performance_analysis",
            "application_analysis": "application_analysis",
        },
    )

    for node in [
        "network_analysis",
        "database_analysis",
        "auth_analysis",
        "performance_analysis",
        "application_analysis",
    ]:
        graph.add_edge(node, "generate_final_report")

    graph.add_edge("generate_final_report", END)

    return graph.compile()


workflow = build_workflow()


def analyze_incident(title: str, description: str, source: str = "unknown") -> IncidentReport:
    result = workflow.invoke(
        {
            "title": title,
            "description": description,
            "source": source,
        }
    )

    return IncidentReport(
        category=result["category"],
        severity=result["severity"],
        summary=result["summary"],
        probable_causes=result["probable_causes"],
        recommended_actions=result["recommended_actions"],
        status=result.get("status", "analysis_complete"),
    )
