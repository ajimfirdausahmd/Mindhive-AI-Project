from fastapi.testclient import TestClient


def test_calc_missing_expr(client: TestClient):
    """
    User says 'Calculate' but doesn't give any numbers.
    Expect: 400/422 + friendly error, not crash.
    """
    # ✅ correct path: /api/v1/calculator
    response = client.get("/api/v1/calculator")  # no expr param
    assert response.status_code in (400, 422)

    data = response.json()
    msg = str(data).lower()
    assert "expr" in msg or "expression" in msg or "missing" in msg


def test_products_missing_query(client: TestClient):
    """
    User says 'Show products' but no query is provided.
    Expect: 400/422 + clear message about missing query.
    """
    # ✅ correct path: /api/v1/products
    response = client.get("/api/v1/products")  # no query param
    assert response.status_code in (400, 422)

    data = response.json()
    msg = str(data).lower()
    assert "query" in msg or "question" in msg or "missing" in msg


def test_outlets_missing_query(client: TestClient):
    """
    User says 'Show outlets' with no natural language query.
    Expect: 400/422 + message hinting what is needed (city/outlet/etc.).
    """
    # ✅ correct path: /api/v1/outlets
    response = client.get("/api/v1/outlets")  # no query param
    assert response.status_code in (400, 422)

    data = response.json()
    msg = str(data).lower()
    assert (
        "query" in msg
        or "city" in msg
        or "outlet" in msg
        or "missing" in msg
    )

