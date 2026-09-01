"""Harden financial and inventory integrity.

Revision ID: c7d5e2a91b44
Revises: 9a271b47863a
Create Date: 2026-08-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7d5e2a91b44"
down_revision: Union[str, Sequence[str], None] = "9a271b47863a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _assert_existing_data_is_safe() -> None:
    """Fail before DDL if legacy rows violate the new financial constraints."""
    checks = {
        "sales with paid_amount greater than total_amount":
            "SELECT count(*) FROM sales WHERE paid_amount > total_amount",
        "purchases with paid_amount greater than total_amount":
            "SELECT count(*) FROM purchases WHERE paid_amount > total_amount",
        "debts with an invalid paid or remaining balance":
            "SELECT count(*) FROM debts "
            "WHERE paid_amount > total_amount OR remaining_amount <> total_amount - paid_amount",
        "sale items with non-positive quantity":
            "SELECT count(*) FROM sale_items WHERE quantity <= 0",
        "purchase items with non-positive quantity":
            "SELECT count(*) FROM purchase_items WHERE quantity <= 0",
        "payments with non-positive amount":
            "SELECT count(*) FROM payments WHERE amount <= 0",
        "expenses with non-positive amount":
            "SELECT count(*) FROM expenses WHERE amount <= 0",
        "zero-quantity stock movements":
            "SELECT count(*) FROM stock_movements WHERE quantity = 0",
    }
    bind = op.get_bind()
    failures = []
    for description, query in checks.items():
        count = int(bind.execute(sa.text(query)).scalar_one())
        if count:
            failures.append(f"{description}: {count}")
    if failures:
        raise RuntimeError(
            "Integrity migration stopped without changing the database. "
            "Correct or explicitly reconcile these legacy rows first: " + "; ".join(failures)
        )


def upgrade() -> None:
    _assert_existing_data_is_safe()
    op.add_column(
        "sale_items",
        sa.Column("cost_price", sa.Numeric(precision=12, scale=2), server_default="0", nullable=False),
    )
    op.execute(
        """
        UPDATE sale_items
        SET cost_price = COALESCE(products.cost_price, 0)
        FROM products
        WHERE sale_items.product_id = products.id
        """
    )
    op.create_check_constraint("check_sitem_cost_positive", "sale_items", "cost_price >= 0")

    op.drop_constraint("check_sitem_qty_positive", "sale_items", type_="check")
    op.create_check_constraint("check_sitem_qty_positive", "sale_items", "quantity > 0")
    op.drop_constraint("check_pitem_qty_positive", "purchase_items", type_="check")
    op.create_check_constraint("check_pitem_qty_positive", "purchase_items", "quantity > 0")
    op.drop_constraint("check_expense_amount_positive", "expenses", type_="check")
    op.create_check_constraint("check_expense_amount_positive", "expenses", "amount > 0")
    op.drop_constraint("check_payment_amount_positive", "payments", type_="check")
    op.create_check_constraint("check_payment_amount_positive", "payments", "amount > 0")

    op.add_column("payments", sa.Column("sale_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_payments_sale_id_sales",
        "payments",
        "sales",
        ["sale_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_payments_sale_id", "payments", ["sale_id"], unique=False)
    op.execute(
        """
        UPDATE payments
        SET sale_id = debts.sale_id
        FROM debts
        WHERE payments.debt_id = debts.id AND payments.sale_id IS NULL
        """
    )

    op.execute(
        "UPDATE sales SET completed_at = COALESCE(completed_at, sale_date, created_at, now()) "
        "WHERE status = 'COMPLETED'"
    )
    op.execute(
        "UPDATE purchases SET completed_at = COALESCE(completed_at, purchase_date, created_at, now()) "
        "WHERE status = 'COMPLETED'"
    )

    op.create_check_constraint("check_sale_paid_not_over_total", "sales", "paid_amount <= total_amount")
    op.create_check_constraint("check_purc_paid_not_over_total", "purchases", "paid_amount <= total_amount")
    op.create_check_constraint("check_debt_paid_not_over_total", "debts", "paid_amount <= total_amount")
    op.create_check_constraint(
        "check_debt_balance_consistent",
        "debts",
        "remaining_amount = total_amount - paid_amount",
    )
    op.create_check_constraint(
        "check_stock_movement_nonzero",
        "stock_movements",
        "quantity <> 0",
    )


def downgrade() -> None:
    op.drop_constraint("check_stock_movement_nonzero", "stock_movements", type_="check")
    op.drop_constraint("check_debt_balance_consistent", "debts", type_="check")
    op.drop_constraint("check_debt_paid_not_over_total", "debts", type_="check")
    op.drop_constraint("check_purc_paid_not_over_total", "purchases", type_="check")
    op.drop_constraint("check_sale_paid_not_over_total", "sales", type_="check")

    op.drop_constraint("check_payment_amount_positive", "payments", type_="check")
    op.create_check_constraint("check_payment_amount_positive", "payments", "amount >= 0")
    op.drop_constraint("check_expense_amount_positive", "expenses", type_="check")
    op.create_check_constraint("check_expense_amount_positive", "expenses", "amount >= 0")
    op.drop_constraint("check_pitem_qty_positive", "purchase_items", type_="check")
    op.create_check_constraint("check_pitem_qty_positive", "purchase_items", "quantity >= 0")
    op.drop_constraint("check_sitem_qty_positive", "sale_items", type_="check")
    op.create_check_constraint("check_sitem_qty_positive", "sale_items", "quantity >= 0")

    op.drop_index("ix_payments_sale_id", table_name="payments")
    op.drop_constraint("fk_payments_sale_id_sales", "payments", type_="foreignkey")
    op.drop_column("payments", "sale_id")

    op.drop_constraint("check_sitem_cost_positive", "sale_items", type_="check")
    op.drop_column("sale_items", "cost_price")
