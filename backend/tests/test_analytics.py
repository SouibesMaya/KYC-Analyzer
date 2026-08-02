EXPECTED_KPI_KEYS = {
    "total_documents",
    "total_cases",
    "emails_sent",
    "compliance_rate",
    "avg_risk_score",
    "mrz_rate",
    "expired_count",
    "by_type",
    "by_status",
    "by_decision",
    "daily_counts",
}


def test_kpis_returns_200(client):
    response = client.get("/api/analytics/kpis")
    assert response.status_code == 200


def test_kpis_contains_essential_keys(client):
    response = client.get("/api/analytics/kpis")
    body = response.json()
    assert EXPECTED_KPI_KEYS.issubset(body.keys())


def test_kpis_accepts_days_filter(client):
    response = client.get("/api/analytics/kpis", params={"days": 30})
    assert response.status_code == 200


def test_kpis_accepts_custom_date_range(client):
    response = client.get(
        "/api/analytics/kpis",
        params={"from_date": "2026-01-01", "to_date": "2026-12-31"},
    )
    assert response.status_code == 200
