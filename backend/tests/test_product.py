from decimal import Decimal

from app.models.product import Product, ProductStatusEnum
from app.models.stock_movement import MovementTypeEnum


def create_product(client, stock="10", sell_price="15", cost_price="10"):
    response = client.post(
        "/api/v1/businesses/1/products",
        json={
            "business_id": 999,
            "name": "Coffee",
            "sku": "COFFEE-1",
            "cost_price": cost_price,
            "sell_price": sell_price,
            "stock_qty": stock,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_opening_stock_creates_audited_movement(client, db_session):
    product = create_product(client)
    movements = client.get("/api/v1/businesses/1/stock-movements").json()

    assert product["stock_qty"] == "10.00"
    assert len(movements) == 1
    assert movements[0]["type"] == MovementTypeEnum.ADJUST.value
    assert movements[0]["quantity"] == "10.00"


def test_stock_cannot_be_changed_through_product_update(client):
    product = create_product(client)
    response = client.put(
        f"/api/v1/businesses/1/products/{product['id']}",
        json={"stock_qty": "999"},
    )
    assert response.status_code == 422


def test_owner_adjustment_cannot_make_stock_negative(client):
    product = create_product(client)
    failed = client.post(
        "/api/v1/businesses/1/stock-adjustments",
        json={"product_id": product["id"], "quantity": "-11", "note": "Count correction"},
    )
    assert failed.status_code == 400

    succeeded = client.post(
        "/api/v1/businesses/1/stock-adjustments",
        json={"product_id": product["id"], "quantity": "-2", "note": "Count correction"},
    )
    assert succeeded.status_code == 200, succeeded.text

    products = client.get("/api/v1/businesses/1/products").json()
    assert products[0]["stock_qty"] == "8.00"


def test_delete_soft_deactivates_product(client, db_session):
    product = create_product(client)
    response = client.delete(f"/api/v1/businesses/1/products/{product['id']}")
    assert response.status_code == 200
    assert client.get("/api/v1/businesses/1/products").json() == []

    stored = db_session.get(Product, product["id"])
    assert stored.status == ProductStatusEnum.INACTIVE
    assert stored.stock_qty == Decimal("10.00")
