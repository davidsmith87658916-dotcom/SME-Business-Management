# SME Business Management Backend

FastAPI backend for multi-business sales, purchases, inventory, expenses, customer debt, payments, dashboard metrics, and reports.

## Requirements

- Python 3.12
- PostgreSQL
- A configured `.env` based on `.env.example`

## Setup

From the project root:

```powershell
Copy-Item backend\.env.example backend\.env
# Edit backend\.env before continuing.
.\setup.ps1
```

The setup command installs the pinned dependencies but intentionally does not
change the database. Back up the PostgreSQL database, review the new migration,
then apply it explicitly:

```powershell
.\setup.ps1 -RunMigrations
```

The integrity migration performs a read-only preflight first. If legacy rows
contain overpayments, inconsistent debt balances, zero-value payments/expenses,
or zero-quantity transaction lines, it stops before changing the schema and
prints the affected row counts. Reconcile those records deliberately rather
than letting a migration guess how financial history should be rewritten.

Run the API from `backend`:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Run tests:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

## Financial and inventory rules

- Sale prices are verified against the current product catalog price.
- Sale, purchase, stock movement, debt, and payment changes are committed atomically.
- Draft sales do not reserve or reduce stock; the completion endpoint rechecks and locks stock before posting the sale.
- Product stock cannot be edited through the product update endpoint; owners must use the stock-adjustment endpoint.
- Stock rows and debt rows are locked during updates to prevent concurrent overselling or overpayment.
- Money is validated and stored with two decimal places.
- Sale items store a cost-price snapshot so historical profit reports do not change when product costs change later.
- Business-scoped foreign IDs are validated before records are created.

Do not commit `.env` or a virtual environment to source control.
