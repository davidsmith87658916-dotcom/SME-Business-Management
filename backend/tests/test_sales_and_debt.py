from app.models.customer import Customer
from app.models.debt import Debt, DebtStatusEnum
from app.models.payment import Payment
from app.models.sale import PaymentStatusEnum, Sale, SaleStatusEnum


def seed_customer_and_product(client):
    customer = client.post(
        "/api/v1/businesses/1/customers",
        json={"business_id": 1, "name": "Customer One"},
    )
    assert customer.status_code == 200, customer.text
    product = client.post(
        "/api/v1/businesses/1/products",
        json={
            "business_id": 1,
            "name": "Latte",
            "sku": "LATTE",
            "cost_price": "4.00",
            "sell_price": "10.00",
            "stock_qty": "10.00",
        },
    )
    assert product.status_code == 200, product.text
    return customer.json(), product.json()


def test_partial_sale_links_payment_and_debt_then_closes_both(client, db_session):
    customer, product = seed_customer_and_product(client)
    response = client.post(
        "/api/v1/businesses/1/sales",
        json={
            "business_id": 999,
            "customer_id": customer["id"],
            "paid_amount": "5.00",
            "payment_method": "CASH",
            "items": [
                {"product_id": product["id"], "quantity": "2.00", "price": "10.00", "discount": "0.00"}
            ],
        },
    )
    assert response.status_code == 200, response.text
    sale_data = response.json()
    assert sale_data["total_amount"] == "20.00"
    assert sale_data["payment_status"] == PaymentStatusEnum.PARTIAL.value

    debt = db_session.query(Debt).filter(Debt.sale_id == sale_data["id"]).one()
    initial_payment = db_session.query(Payment).filter(Payment.sale_id == sale_data["id"]).one()
    assert initial_payment.debt_id == debt.id
    assert debt.remaining_amount == 15

    payment_response = client.post(
        f"/api/v1/businesses/1/debts/{debt.id}/payments",
        json={
            "amount": "15.00",
            "payment_method": "BANK",
            "note": "Final settlement",
            "payment_date": "2026-08-27T10:00:00+00:00",
        },
    )
    assert payment_response.status_code == 200, payment_response.text
    assert payment_response.json()["note"] == "Final settlement"

    db_session.expire_all()
    debt = db_session.get(Debt, debt.id)
    sale = db_session.get(Sale, sale_data["id"])
    assert debt.status == DebtStatusEnum.PAID
    assert debt.remaining_amount == 0
    assert sale.payment_status == PaymentStatusEnum.PAID
    assert sale.paid_amount == sale.total_amount

    products = client.get("/api/v1/businesses/1/products").json()
    assert products[0]["stock_qty"] == "8.00"


def test_duplicate_product_lines_are_rejected_before_stock_changes(client):
    customer, product = seed_customer_and_product(client)
    response = client.post(
        "/api/v1/businesses/1/sales",
        json={
            "customer_id": customer["id"],
            "items": [
                {"product_id": product["id"], "quantity": "6", "price": "10"},
                {"product_id": product["id"], "quantity": "6", "price": "10"},
            ],
        },
    )
    assert response.status_code == 400
    products = client.get("/api/v1/businesses/1/products").json()
    assert products[0]["stock_qty"] == "10.00"


def test_catalog_price_and_discount_are_server_enforced(client):
    customer, product = seed_customer_and_product(client)
    wrong_price = client.post(
        "/api/v1/businesses/1/sales",
        json={
            "customer_id": customer["id"],
            "items": [{"product_id": product["id"], "quantity": "1", "price": "0.01"}],
        },
    )
    assert wrong_price.status_code == 400

    excessive_discount = client.post(
        "/api/v1/businesses/1/sales",
        json={
            "customer_id": customer["id"],
            "items": [{"product_id": product["id"], "quantity": "1", "price": "10", "discount": "11"}],
        },
    )
    assert excessive_discount.status_code == 400


def test_cross_business_customer_is_rejected(client, db_session):
    _, product = seed_customer_and_product(client)
    from app.models.business import Business

    db_session.add(Business(id=2, name="Other Business"))
    db_session.flush()
    other_customer = Customer(business_id=2, name="Private Customer")
    db_session.add(other_customer)
    db_session.commit()

    response = client.post(
        "/api/v1/businesses/1/sales",
        json={
            "customer_id": other_customer.id,
            "items": [{"product_id": product["id"], "quantity": "1", "price": "10"}],
        },
    )
    assert response.status_code == 400


def test_zero_debt_payment_is_rejected_by_schema(client):
    customer, product = seed_customer_and_product(client)
    sale = client.post(
        "/api/v1/businesses/1/sales",
        json={
            "customer_id": customer["id"],
            "paid_amount": "0",
            "items": [{"product_id": product["id"], "quantity": "1", "price": "10"}],
        },
    ).json()
    debts = client.get("/api/v1/businesses/1/debts").json()
    response = client.post(
        f"/api/v1/businesses/1/debts/{debts[0]['id']}/payments",
        json={"amount": "0", "payment_method": "CASH"},
    )
    assert sale["payment_status"] == PaymentStatusEnum.UNPAID.value
    assert response.status_code == 422


def test_draft_sale_does_not_touch_stock_until_completion(client, db_session):
    _, product = seed_customer_and_product(client)
    draft_response = client.post(
        "/api/v1/businesses/1/sales",
        json={
            "save_as_draft": True,
            "items": [{"product_id": product["id"], "quantity": "2", "price": "10"}],
        },
    )
    assert draft_response.status_code == 200, draft_response.text
    draft = draft_response.json()
    assert draft["status"] == SaleStatusEnum.DRAFT.value
    assert client.get("/api/v1/businesses/1/products").json()[0]["stock_qty"] == "10.00"
    assert client.get("/api/v1/businesses/1/dashboard").json()["new_orders_count"] == 1
    assert db_session.query(Payment).count() == 0
    assert db_session.query(Debt).count() == 0

    unpaid_without_customer = client.post(
        f"/api/v1/businesses/1/sales/{draft['id']}/complete",
        json={"paid_amount": "0"},
    )
    assert unpaid_without_customer.status_code == 400
    assert client.get("/api/v1/businesses/1/products").json()[0]["stock_qty"] == "10.00"

    completion = client.post(
        f"/api/v1/businesses/1/sales/{draft['id']}/complete",
        json={"paid_amount": "20", "payment_method": "CASH"},
    )
    assert completion.status_code == 200, completion.text
    assert completion.json()["status"] == SaleStatusEnum.COMPLETED.value
    assert completion.json()["payment_status"] == PaymentStatusEnum.PAID.value
    assert client.get("/api/v1/businesses/1/products").json()[0]["stock_qty"] == "8.00"
    assert client.get("/api/v1/businesses/1/dashboard").json()["new_orders_count"] == 0
    assert db_session.query(Payment).count() == 1
