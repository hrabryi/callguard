import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_simulate_safe_continue(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/simulate/scenario",
        json={"scenario": "safe_continue"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario"] == "safe_continue"

    call = data["call"]
    assert len(call["events"]) > 0
    assert call["decisions"][0]["decision"] == "continue"


@pytest.mark.asyncio
async def test_simulate_cancel_order_unverified(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/simulate/scenario",
        json={"scenario": "cancel_order_unverified"},
    )
    assert resp.status_code == 200
    data = resp.json()

    call = data["call"]
    assert call["status"] == "handed_off"
    assert call["decisions"][0]["decision"] == "handoff"
    assert len(call["handoff_summaries"]) == 1


@pytest.mark.asyncio
async def test_simulate_downstream_failure(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/simulate/scenario",
        json={"scenario": "downstream_failure"},
    )
    assert resp.status_code == 200
    data = resp.json()

    call = data["call"]
    assert call["decisions"][0]["decision"] == "handoff"
    assert call["decisions"][0]["reason"] == "downstream_api_failed"


@pytest.mark.asyncio
async def test_list_scenarios(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/simulate/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert "safe_continue" in data
    assert "cancel_order_unverified" in data
    assert "downstream_failure" in data
