from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest

@pytest.mark.skip(reason="Update monkeypatch target to match your products logic, then remove this skip")
def test_products_api_downtime(client: TestClient, monkeypatch):
    """
    Simulate upstream failure in /products endpoint.

    You MUST change:
        from app.routers import products as products_router
        monkeypatch.setattr(products_router, "handle_products_query", ...)
    to match your real function name.
    """
    from api.routers import products as products_router 

    def fake_handle_products_query(*args, **kwargs):
        raise HTTPException(status_code=500, detail="Upstream service down")

    monkeypatch.setattr(
        products_router, "handle_products_query", fake_handle_products_query
    )

    response = client.get("/api/v1/products",params={"query": "Show me tumblers"})
    assert response.status_code in (500, 503)

    data = response.json()
    msg = str(data).lower()
    assert "down" in msg or "unavailable" in msg or "try again" in msg


@pytest.mark.skip(reason="Update monkeypatch target to match your outlets logic, then remove this skip")
def test_outlets_api_downtime(client: TestClient, monkeypatch):
    """
    Simulate database or service failure in /outlets endpoint.

    Same idea: update the function name to whatever your router uses internally.
    """
    from api.routers import outlets as outlets_router  

    def fake_handle_outlets_query(*args, **kwargs):
        raise HTTPException(status_code=500, detail="Database not reachable")

    monkeypatch.setattr(
        outlets_router, "handle_outlets_query", fake_handle_outlets_query
    )

    response = client.get(
        "/api/v1/outlets", params={"query": "Is there an outlet in Petaling Jaya?"}
    )
    assert response.status_code in (500, 503)

    data = response.json()
    msg = str(data).lower()
    assert "unavailable" in msg or "try again" in msg or "down" in msg