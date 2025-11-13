from fastapi.testclient import TestClient


def test_outlets_sql_injection_rejected(client: TestClient):
    """
    User tries SQL injection-like payload.
    Expectation for this project:
    - The system MUST NOT crash
    - The system MUST NOT execute unsafe SQL
    - It's acceptable to return 404 (no outlets found) or 200 with safe data
    """
    injection_payload = "Wangsa Maju'; DROP TABLE outlets; --"

    response = client.get("/api/v1/outlets", params={"query": injection_payload})

    assert response.status_code in (200, 400, 404, 422)

    data = response.json()

    if response.status_code == 404:
        assert isinstance(data, dict)
        assert "detail" in data
        assert "no outlets" in data["detail"].lower()
    else:
        assert isinstance(data, list)
        if data:  
            row = data[0]
            assert "city" in row
            assert "outlet" in row
            assert "open_time" in row
            assert "close_time" in row


def test_outlets_unsafe_sql_guard_message(client: TestClient):
    """
    Dangerous-looking natural language (with 'DROP TABLE') should still:
    - not crash
    - not execute unsafe SQL
    - typically return 200 with safe results
    """
    dangerous_query = "show me everything; DROP TABLE outlets;"

    response = client.get("/api/v1/outlets", params={"query": dangerous_query})

    # For your current implementation, this returns 200 with safe SELECT.
    assert response.status_code in (200, 400, 404, 422)

    data = response.json()

    if response.status_code == 200:
        assert isinstance(data, list)
        assert len(data) > 0  
        sample = data[0]
        assert "city" in sample
        assert "outlet" in sample
        assert "open_time" in sample
        assert "close_time" in sample
    else:
        assert isinstance(data, dict)
        assert "detail" in data