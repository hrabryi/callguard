import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_create_call(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/calls", json={"caller_phone": "+13105551234"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "active"
    assert data["caller_phone"] == "+13105551234"
    assert "external_id" in data


@pytest.mark.asyncio
async def test_process_utterance_safe_continue(client: AsyncClient) -> None:
    call_resp = await client.post("/api/v1/calls", json={"caller_phone": "+13105551234"})
    call_id = call_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/calls/{call_id}/utterances",
        json={"text": "Where is my order #12345?", "verified": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "check_order_status"
    assert data["decision"] == "continue"
    assert data["handoff_summary"] is None


@pytest.mark.asyncio
async def test_process_utterance_handoff(client: AsyncClient) -> None:
    call_resp = await client.post("/api/v1/calls", json={"caller_phone": "+13105551234"})
    call_id = call_resp.json()["id"]

    resp = await client.post(
        f"/api/v1/calls/{call_id}/utterances",
        json={"text": "I want to cancel my order", "verified": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "cancel_order"
    assert data["decision"] == "handoff"
    assert data["handoff_summary"] is not None


@pytest.mark.asyncio
async def test_get_call_detail_with_timeline(client: AsyncClient) -> None:
    call_resp = await client.post("/api/v1/calls", json={"caller_phone": "+13105551234"})
    call_id = call_resp.json()["id"]

    await client.post(
        f"/api/v1/calls/{call_id}/utterances",
        json={"text": "Where is my order?", "verified": True},
    )

    resp = await client.get(f"/api/v1/calls/{call_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["events"]) > 0
    assert len(data["decisions"]) == 1

    event_types = [e["event_type"] for e in data["events"]]
    assert "utterance_received" in event_types
    assert "intent_predicted" in event_types
    assert "decision_made" in event_types


@pytest.mark.asyncio
async def test_call_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/calls/9999")
    assert resp.status_code == 404
