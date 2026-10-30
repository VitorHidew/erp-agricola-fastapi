from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_auth_status():
    with TestClient(app) as client:
        r = client.get("/api/auth/status")
        assert r.status_code == 200
        assert "api_key_required" in r.json()


def test_health():
    with TestClient(app) as client:
        r = client.get("/api/system/health")
        assert r.status_code == 200
        j = r.json()
        assert j["ok"] is True
        assert j["products"] > 50


def test_orders_list_with_lines():
    with TestClient(app) as client:
        r = client.get("/api/orders")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        orders = data["items"]
        assert isinstance(orders, list)
        assert len(orders) > 0
        assert "lines" in orders[0]


def test_finance_entries_paginated():
    with TestClient(app) as client:
        r = client.get("/api/finance/entries?page=1&page_size=10")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and "total" in data
        assert isinstance(data["items"], list)


def test_orders_draft_ids():
    with TestClient(app) as client:
        r = client.get("/api/orders/draft-ids")
        assert r.status_code == 200
        data = r.json()
        assert "ids" in data and "total" in data
        assert isinstance(data["ids"], list)


def test_create_multiline_order():
    with TestClient(app) as client:
        payload = {
            "order_code": "PED-TEST-MULTI-0001",
            "order_date": "2026-05-01",
            "order_type": "Venda",
            "status": "Rascunho",
            "party_name": "Cliente Teste",
            "delivery_date": "2026-05-10",
            "discount_order_pct": 2,
            "lines": [
                {"product_sku": "AGR-1000", "volume_m3": 1, "unit_price": 8, "discount_line_pct": 0},
                {"product_sku": "AGR-1001", "volume_m3": 2, "unit_price": 6, "discount_line_pct": 5},
            ],
        }
        r = client.post("/api/orders", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert len(data["lines"]) == 2
        assert data["total_value"] > 0


def test_negative_stock_movement_blocked():
    with TestClient(app) as client:
        payload = {
            "movement_type": "Saída",
            "movement_date": "2026-05-04",
            "product_sku": "AGR-1000",
            "volume_m3": 1_000_000,
        }
        r = client.post("/api/movements", json=payload)
        assert r.status_code == 400


def test_catalog_is_public_and_uses_agricultural_units():
    with TestClient(app) as client:
        r = client.get("/api/catalog/products")
        assert r.status_code == 200
        products = r.json()
        assert len(products) > 0
        assert products[0]["unit"] in {"kg", "unidade", "maço", "caixa", "bandeja", "dúzia", "litro", "pote", "frasco"}


def test_search_contract_is_grouped_for_frontend():
    with TestClient(app) as client:
        r = client.get("/api/search?q=AGR")
        assert r.status_code == 200
        data = r.json()
        assert "results" in data
        assert "products" in data
        assert "parties" in data
        assert "orders" in data


def test_duplicate_sku_is_rejected():
    payload = {
        "sku": "AGR-UNICO-1",
        "name": "Produto de teste",
        "category": "Hortaliças",
        "unit": "kg",
    }
    with TestClient(app) as client:
        assert client.post("/api/products", json=payload).status_code == 200
        assert client.post("/api/products", json=payload).status_code == 409


def test_demo_reset_is_disabled_by_default():
    with TestClient(app) as client:
        r = client.post("/api/dev/load-mock")
        assert r.status_code == 403

