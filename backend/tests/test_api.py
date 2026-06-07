"""End-to-end API tests using an in-memory SQLite DB and the rule-based engine."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("LLM_PROVIDER", "none")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_parse(client):
    r = client.post("/api/parse", json={"query": "phone with great camera under 50000, not Apple"})
    assert r.status_code == 200
    body = r.json()
    assert body["requirement"]["category"] == "smartphone"
    assert "apple" in body["requirement"]["avoided_brands"]


def test_match_returns_ranked_results(client):
    r = client.post("/api/match", json={
        "requirement": {"category": "smartphone", "budget_max": 70000, "priorities": ["camera"]},
        "limit": 5,
    })
    assert r.status_code == 200
    results = r.json()["results"]
    assert len(results) >= 1
    scores = [x["match_score"] for x in results]
    assert scores == sorted(scores, reverse=True)  # ranked descending


def test_price_check_flags_fake_discount(client):
    r = client.post("/api/price-check", json={"product_id": "iphone16pro", "urgency": "can_wait"})
    assert r.status_code == 200
    assert "fake_discount_analysis" in r.json()


def test_auth_flow_and_alert(client):
    email = "rahul@example.com"
    reg = client.post("/api/auth/register", json={"email": email, "password": "supersecret1"})
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200 and me.json()["email"] == email

    created = client.post("/api/alerts", headers=headers, json={
        "product_id": "iphone16pro", "product_name": "iPhone 16 Pro", "target_price": 115000})
    assert created.status_code == 201

    listed = client.get("/api/alerts", headers=headers)
    assert listed.status_code == 200 and len(listed.json()) == 1


def test_alert_requires_auth(client):
    r = client.post("/api/alerts", json={
        "product_id": "x", "product_name": "y", "target_price": 100})
    assert r.status_code == 401


def test_chat_rule_based(client):
    r = client.post("/api/chat", json={"query": "good camera phone under 70000"})
    assert r.status_code == 200
    assert r.json()["answer_source"] == "rule_based"


def test_discover_mock_provider(client):
    r = client.post("/api/discover", json={"query": "samsung", "category": "smartphone", "limit": 5})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "MockProvider"
    assert isinstance(body["results"], list) and len(body["results"]) >= 1
