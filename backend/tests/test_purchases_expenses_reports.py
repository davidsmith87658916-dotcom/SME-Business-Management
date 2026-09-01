from decimal import Decimal

from app.models.business import Business
from app.models.expense_category import ExpenseCategory
from app.models.supplier import Supplier


def seed_product(client):
    response = client.post(
        "/api/v1/businesses/1/products",
        json={
            "name": "Tea",
            "sku": "TEA",
            "cost_price": "2.00",
            "sell_price": "5.00",
            "stock_qty": "10.00",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def seed_supplier(client):
    response = client.post(
        "/api/v1/businesses/1/suppliers",
        json={"business_id": 1, "name": "Supplier One"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_purchase_updates_stock_weighted_cost_and_rejects_overpayment(client):
    product = seed_product(client)
    supplier = seed_supplier(client)

    overpayment = client.post(
        "/api/v1/businesses/1/purchases",
        json={
            "supplier_id": supplier["id"],
            "paid_amount": "100",
            "items": [{"product_id": product["id"], "quantity": "10", "cost_price": "4"}],
        },
    )
    assert overpayment.status_code == 400

    response = client.post(
        "/api/v1/businesses/1/purchases",
        json={
            "supplier_id": supplier["id"],
            "paid_amount": "40",
            "purchase_date": "2026-08-27T09:00:00+00:00",
            "items": [{"product_id": product["id"], "quantity": "10", "cost_price": "4"}],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["completed_at"] is not None

    updated = client.get("/api/v1/businesses/1/products").json()[0]
    assert updated["stock_qty"] == "20.00"
    assert updated["cost_price"] == "3.00"


def test_cross_business_supplier_and_expense_category_are_rejected(client, db_session):
    product = seed_product(client)
    db_session.add(Business(id=2, name="Other Business"))
    db_session.flush()
    supplier = Supplier(business_id=2, name="Other Supplier")
    category = ExpenseCategory(business_id=2, name="Private Category")
    db_session.add_all([supplier, category])
    db_session.commit()

    purchase = client.post(
        "/api/v1/businesses/1/purchases",
        json={
            "supplier_id": supplier.id,
            "items": [{"product_id": product["id"], "quantity": "1", "cost_price": "1"}],
        },
    )
    assert purchase.status_code == 400

    expense = client.post(
        "/api/v1/businesses/1/expenses",
        json={"category_id": category.id, "title": "Should fail", "amount": "5"},
    )
    assert expense.status_code == 400


def test_profit_uses_cost_snapshot_and_invoice_discount(client):
    customer = client.post(
        "/api/v1/businesses/1/customers",
        json={"name": "Report Customer"},
    ).json()
    product = seed_product(client)
    sale = client.post(
        "/api/v1/businesses/1/sales",
        json={
            "customer_id": customer["id"],
            "paid_amount": "9.00",
            "discount_amount": "1.00",
            "items": [{"product_id": product["id"], "quantity": "2", "price": "5"}],
        },
    )
    assert sale.status_code == 200, sale.text

    expense = client.post(
        "/api/v1/businesses/1/expenses",
        json={"title": "Delivery", "amount": "1.00"},
    )
    assert expense.status_code == 200, expense.text

    sales_report = client.get("/api/v1/businesses/1/reports/sales").json()
    profit_report = client.get("/api/v1/businesses/1/reports/profit").json()

    assert Decimal(sales_report["total_sales_amount"]) == Decimal("9.00")
    assert Decimal(sales_report["top_selling_products"][0]["total_revenue"]) == Decimal("9.00")
    assert Decimal(profit_report["total_cogs"]) == Decimal("4.00")
    assert Decimal(profit_report["total_expenses"]) == Decimal("1.00")
    assert Decimal(profit_report["net_profit"]) == Decimal("4.00")
