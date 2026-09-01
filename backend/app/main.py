from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, businesses, products, customers, suppliers, sales, purchases, expenses, debts, dashboard, reports
from app.config import settings

app = FastAPI(title="SME Business Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(businesses.router, prefix="/api/v1/businesses", tags=["businesses"])
app.include_router(products.router, prefix="/api/v1/businesses", tags=["products"])
app.include_router(customers.router, prefix="/api/v1/businesses", tags=["customers"])
app.include_router(suppliers.router, prefix="/api/v1/businesses", tags=["suppliers"])
app.include_router(sales.router, prefix="/api/v1/businesses", tags=["sales"])
app.include_router(purchases.router, prefix="/api/v1/businesses", tags=["purchases"])
app.include_router(expenses.router, prefix="/api/v1/businesses", tags=["expenses"])
app.include_router(debts.router, prefix="/api/v1/businesses", tags=["debts"])
app.include_router(dashboard.router, prefix="/api/v1/businesses", tags=["dashboard"])
app.include_router(reports.router, prefix="/api/v1/businesses", tags=["reports"])

@app.get("/")
def root():
    return {"message": "Welcome to SME Business Management API"}
