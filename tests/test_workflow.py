from app.workflow import analyze_incident


def test_database_incident():
    report = analyze_incident(
        title="Database connection failures",
        description=(
            "Production API requests are failing with repeated connection pool "
            "exhaustion and database timeout errors."
        ),
        source="production-api",
    )

    assert report.category == "database"
    assert report.severity in {"high", "critical"}
    assert len(report.probable_causes) > 0
    assert len(report.recommended_actions) > 0


def test_authentication_incident():
    report = analyze_incident(
        title="Users cannot log in",
        description="Authentication tokens are rejected as unauthorized after deployment.",
        source="auth-service",
    )

    assert report.category == "authentication"
    assert len(report.recommended_actions) > 0


def test_network_incident():
    report = analyze_incident(
        title="Service cannot reach upstream API",
        description="TCP connection refused and DNS lookup failures appear in logs.",
        source="gateway",
    )

    assert report.category == "network"
