from datetime import date as date_cls
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import Backend.models as models
import Backend.schemas as schemas
import Backend.accounting as accounting
import Backend.reports as reports
import Backend.gemini as gemini
from Backend.database import get_db, init_db
from Backend.auth import (
    hash_password, verify_password, create_access_token, get_current_user
)

app = FastAPI(
    title="Urban Furniture Accounting System",
    description="Simple accounting backend for a furniture business.",
    version="1.0.0",
)

# CORS - allow the React/Vite frontend (running on any localhost port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


def error(detail: str, code: int = status.HTTP_400_BAD_REQUEST):
    raise HTTPException(status_code=code, detail=detail)


# =========================================================
# AUTH
# =========================================================

@app.post("/auth/login", response_model=schemas.Token, tags=["Auth"])
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        error("Incorrect email or password", status.HTTP_401_UNAUTHORIZED)

    token = create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=token)


@app.get("/auth/me", response_model=schemas.UserOut, tags=["Auth"])
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


# =========================================================
# CONTACTS
# =========================================================

@app.get("/contacts", response_model=List[schemas.ContactOut], tags=["Contacts"])
def list_contacts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Contact).all()


@app.post("/contacts", response_model=schemas.ContactOut, status_code=status.HTTP_201_CREATED, tags=["Contacts"])
def create_contact(payload: schemas.ContactCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    contact = models.Contact(**payload.model_dump())
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@app.put("/contacts/{contact_id}", response_model=schemas.ContactOut, tags=["Contacts"])
def update_contact(contact_id: int, payload: schemas.ContactUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        error("Contact not found", status.HTTP_404_NOT_FOUND)
    for key, value in payload.model_dump().items():
        setattr(contact, key, value)
    db.commit()
    db.refresh(contact)
    return contact


@app.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Contacts"])
def delete_contact(contact_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        error("Contact not found", status.HTTP_404_NOT_FOUND)
    db.delete(contact)
    db.commit()
    return None


# =========================================================
# CATEGORIES
# =========================================================

@app.get("/categories", response_model=List[schemas.CategoryOut], tags=["Categories"])
def list_categories(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Category).all()


@app.post("/categories", response_model=schemas.CategoryOut, status_code=status.HTTP_201_CREATED, tags=["Categories"])
def create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    existing = db.query(models.Category).filter(models.Category.name == payload.name).first()
    if existing:
        error("Category with this name already exists", status.HTTP_409_CONFLICT)
    category = models.Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# =========================================================
# PRODUCTS
# =========================================================

@app.get("/products", response_model=List[schemas.ProductOut], tags=["Products"])
def list_products(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Product).all()


@app.post("/products", response_model=schemas.ProductOut, status_code=status.HTTP_201_CREATED, tags=["Products"])
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if payload.category_id:
        category = db.query(models.Category).filter(models.Category.id == payload.category_id).first()
        if not category:
            error("Category not found", status.HTTP_404_NOT_FOUND)
    product = models.Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@app.put("/products/{product_id}", response_model=schemas.ProductOut, tags=["Products"])
def update_product(product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        error("Product not found", status.HTTP_404_NOT_FOUND)
    for key, value in payload.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Products"])
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        error("Product not found", status.HTTP_404_NOT_FOUND)
    db.delete(product)
    db.commit()
    return None


# =========================================================
# ACCOUNTS
# =========================================================

@app.get("/accounts", response_model=List[schemas.AccountOut], tags=["Accounts"])
def list_accounts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Account).all()


@app.post("/accounts", response_model=schemas.AccountOut, status_code=status.HTTP_201_CREATED, tags=["Accounts"])
def create_account(payload: schemas.AccountCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    existing = db.query(models.Account).filter(models.Account.code == payload.code).first()
    if existing:
        error("Account with this code already exists", status.HTTP_409_CONFLICT)
    account = models.Account(**payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@app.put("/accounts/{account_id}", response_model=schemas.AccountOut, tags=["Accounts"])
def update_account(account_id: int, payload: schemas.AccountUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if not account:
        error("Account not found", status.HTTP_404_NOT_FOUND)
    for key, value in payload.model_dump().items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


# =========================================================
# JOURNALS
# =========================================================

@app.get("/journals", response_model=List[schemas.JournalOut], tags=["Journals"])
def list_journals(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Journal).all()


@app.post("/journals", response_model=schemas.JournalOut, status_code=status.HTTP_201_CREATED, tags=["Journals"])
def create_journal(payload: schemas.JournalCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    journal = models.Journal(**payload.model_dump())
    db.add(journal)
    db.commit()
    db.refresh(journal)
    return journal


@app.put("/journals/{journal_id}", response_model=schemas.JournalOut, tags=["Journals"])
def update_journal(journal_id: int, payload: schemas.JournalUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    journal = db.query(models.Journal).filter(models.Journal.id == journal_id).first()
    if not journal:
        error("Journal not found", status.HTTP_404_NOT_FOUND)
    for key, value in payload.model_dump().items():
        setattr(journal, key, value)
    db.commit()
    db.refresh(journal)
    return journal


# =========================================================
# SALES
# =========================================================

@app.get("/sales", response_model=List[schemas.SaleOut], tags=["Sales"])
def list_sales(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Sale).all()


@app.get("/sales/{sale_id}", response_model=schemas.SaleOut, tags=["Sales"])
def get_sale(sale_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not sale:
        error("Sale not found", status.HTTP_404_NOT_FOUND)
    return sale


@app.post("/sales", response_model=schemas.SaleOut, status_code=status.HTTP_201_CREATED, tags=["Sales"])
def create_sale(payload: schemas.SaleCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    customer = db.query(models.Contact).filter(models.Contact.id == payload.customer_id).first()
    if not customer:
        error("Customer (contact) not found", status.HTTP_404_NOT_FOUND)
    if customer.type not in (models.ContactType.CUSTOMER, models.ContactType.BOTH):
        error("Selected contact is not a CUSTOMER", status.HTTP_400_BAD_REQUEST)

    product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
    if not product:
        error("Product not found", status.HTTP_404_NOT_FOUND)

    if payload.quantity <= 0:
        error("Quantity must be greater than zero")

    if product.type == models.ProductType.GOODS:
        available_stock = accounting.get_product_stock(db, product.id)
        if payload.quantity > available_stock:
            error(
                f"Insufficient stock for product {product.name}: "
                f"requested {payload.quantity}, available {available_stock}",
                status.HTTP_400_BAD_REQUEST,
            )

    # Backend always calculates the real figures - never trust frontend totals
    unit_price = payload.unit_price if payload.unit_price is not None else product.sales_price
    if unit_price < 0:
        error("Unit price cannot be negative")

    subtotal = round(unit_price * payload.quantity, 2)
    tax_percent = payload.tax_percent or 0.0
    tax = round(subtotal * (tax_percent / 100.0), 2)
    total = round(subtotal + tax, 2)

    try:
        sale = models.Sale(
            customer_id=payload.customer_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            unit_price=unit_price,
            tax=tax,
            total=total,
            date=payload.date or date_cls.today(),
            status=models.TxnStatus.CONFIRMED,
        )
        db.add(sale)
        db.flush()  # get sale.id without committing

        # Post journal entry (raises HTTPException if unbalanced)
        accounting.post_sale_entry(db, sale)

        # Record stock movement (goods leaving inventory)
        stock_move = models.StockMovement(
            product_id=product.id,
            type=models.StockMovementType.SALE_OUT,
            quantity=payload.quantity,
            reference_id=sale.id,
            date=sale.date,
        )
        db.add(stock_move)

        db.commit()
        db.refresh(sale)
        return sale
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        error(f"Failed to create sale: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================================================
# PURCHASES
# =========================================================

@app.get("/purchases", response_model=List[schemas.PurchaseOut], tags=["Purchases"])
def list_purchases(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Purchase).all()


@app.get("/purchases/{purchase_id}", response_model=schemas.PurchaseOut, tags=["Purchases"])
def get_purchase(purchase_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    purchase = db.query(models.Purchase).filter(models.Purchase.id == purchase_id).first()
    if not purchase:
        error("Purchase not found", status.HTTP_404_NOT_FOUND)
    return purchase


@app.post("/purchases", response_model=schemas.PurchaseOut, status_code=status.HTTP_201_CREATED, tags=["Purchases"])
def create_purchase(payload: schemas.PurchaseCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    vendor = db.query(models.Contact).filter(models.Contact.id == payload.vendor_id).first()
    if not vendor:
        error("Vendor (contact) not found", status.HTTP_404_NOT_FOUND)
    if vendor.type not in (models.ContactType.VENDOR, models.ContactType.BOTH):
        error("Selected contact is not a VENDOR", status.HTTP_400_BAD_REQUEST)

    product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
    if not product:
        error("Product not found", status.HTTP_404_NOT_FOUND)

    if payload.quantity <= 0:
        error("Quantity must be greater than zero")

    unit_price = payload.unit_price if payload.unit_price is not None else product.purchase_price
    if unit_price < 0:
        error("Unit price cannot be negative")

    subtotal = round(unit_price * payload.quantity, 2)
    tax_percent = payload.tax_percent or 0.0
    tax = round(subtotal * (tax_percent / 100.0), 2)
    total = round(subtotal + tax, 2)

    try:
        purchase = models.Purchase(
            vendor_id=payload.vendor_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            unit_price=unit_price,
            tax=tax,
            total=total,
            date=payload.date or date_cls.today(),
            status=models.TxnStatus.CONFIRMED,
        )
        db.add(purchase)
        db.flush()

        accounting.post_purchase_entry(db, purchase)

        stock_move = models.StockMovement(
            product_id=product.id,
            type=models.StockMovementType.PURCHASE_IN,
            quantity=payload.quantity,
            reference_id=purchase.id,
            date=purchase.date,
        )
        db.add(stock_move)

        db.commit()
        db.refresh(purchase)
        return purchase
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        error(f"Failed to create purchase: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================================================
# PAYMENTS
# =========================================================

@app.get("/payments", response_model=List[schemas.PaymentOut], tags=["Payments"])
def list_payments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Payment).all()


@app.post("/payments", response_model=schemas.PaymentOut, status_code=status.HTTP_201_CREATED, tags=["Payments"])
def create_payment(payload: schemas.PaymentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    contact = db.query(models.Contact).filter(models.Contact.id == payload.contact_id).first()
    if not contact:
        error("Contact not found", status.HTTP_404_NOT_FOUND)

    if payload.amount <= 0:
        error("Payment amount must be greater than zero")

    # Validate payment does not exceed outstanding amount
    if payload.reference_id is not None:
        if payload.type == models.PaymentType.RECEIVE:
            if contact.type not in (models.ContactType.CUSTOMER, models.ContactType.BOTH):
                error("A RECEIVE payment requires a CUSTOMER contact")
            sale = db.query(models.Sale).filter(models.Sale.id == payload.reference_id).first()
            if not sale:
                error("Referenced sale not found", status.HTTP_404_NOT_FOUND)
            if sale.customer_id != contact.id:
                error("Referenced sale does not belong to the selected contact")
            outstanding = accounting.get_sale_outstanding(db, sale)
        else:
            if contact.type not in (models.ContactType.VENDOR, models.ContactType.BOTH):
                error("A PAY payment requires a VENDOR contact")
            purchase = db.query(models.Purchase).filter(models.Purchase.id == payload.reference_id).first()
            if not purchase:
                error("Referenced purchase not found", status.HTTP_404_NOT_FOUND)
            if purchase.vendor_id != contact.id:
                error("Referenced purchase does not belong to the selected contact")
            outstanding = accounting.get_purchase_outstanding(db, purchase)

        if payload.amount > outstanding + 0.000001:
            error(
                f"Payment amount ({payload.amount}) exceeds outstanding amount ({outstanding})",
                status.HTTP_400_BAD_REQUEST,
            )
    else:
        # No specific reference - validate against total outstanding for the contact
        is_customer = payload.type == models.PaymentType.RECEIVE
        if is_customer and contact.type not in (models.ContactType.CUSTOMER, models.ContactType.BOTH):
            error("A RECEIVE payment requires a CUSTOMER contact")
        if not is_customer and contact.type not in (models.ContactType.VENDOR, models.ContactType.BOTH):
            error("A PAY payment requires a VENDOR contact")
        outstanding = accounting.get_contact_outstanding(db, contact.id, is_customer)
        if payload.amount > outstanding + 0.000001:
            error(
                f"Payment amount ({payload.amount}) exceeds total outstanding amount ({outstanding})",
                status.HTTP_400_BAD_REQUEST,
            )

    try:
        payment = models.Payment(
            contact_id=payload.contact_id,
            reference_id=payload.reference_id,
            type=payload.type,
            method=payload.method,
            amount=payload.amount,
            date=payload.date or date_cls.today(),
        )
        db.add(payment)
        db.flush()

        accounting.post_payment_entry(db, payment)

        db.commit()
        db.refresh(payment)
        return payment
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        error(f"Failed to create payment: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================================================
# BUDGETS
# =========================================================

@app.get("/budgets", response_model=List[schemas.BudgetOut], tags=["Budgets"])
def list_budgets(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Budget).all()


@app.post("/budgets", response_model=schemas.BudgetOut, status_code=status.HTTP_201_CREATED, tags=["Budgets"])
def create_budget(payload: schemas.BudgetCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    analytic = db.query(models.AnalyticAccount).filter(models.AnalyticAccount.id == payload.analytic_account_id).first()
    if not analytic:
        error("Analytic account not found", status.HTTP_404_NOT_FOUND)
    if payload.period_end < payload.period_start:
        error("period_end must be after period_start")
    budget = models.Budget(**payload.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@app.put("/budgets/{budget_id}", response_model=schemas.BudgetOut, tags=["Budgets"])
def update_budget(budget_id: int, payload: schemas.BudgetUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    budget = db.query(models.Budget).filter(models.Budget.id == budget_id).first()
    if not budget:
        error("Budget not found", status.HTTP_404_NOT_FOUND)
    if payload.period_end < payload.period_start:
        error("period_end must be after period_start")
    for key, value in payload.model_dump().items():
        setattr(budget, key, value)
    db.commit()
    db.refresh(budget)
    return budget


# =========================================================
# REPORTS
# =========================================================

@app.get("/reports/profit-loss", tags=["Reports"])
def report_profit_loss(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return reports.profit_and_loss(db)


@app.get("/reports/balance-sheet", tags=["Reports"])
def report_balance_sheet(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return reports.balance_sheet(db)


@app.get("/reports/budget", tags=["Reports"])
def report_budget(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return reports.budget_report(db)


@app.get("/reports/stock", tags=["Reports"])
def report_stock(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return reports.stock_report(db)


@app.get("/reports/trial-balance", tags=["Reports"])
def report_trial_balance(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return reports.trial_balance(db)


# =========================================================
# AI
# =========================================================

@app.post("/ai/analyze-report", response_model=schemas.AnalyzeReportResponse, tags=["AI"])
def ai_analyze_report(payload: schemas.AnalyzeReportRequest, current_user: models.User = Depends(get_current_user)):
    # Gemini is only ever given already-calculated figures (payload.data) -
    # it never computes accounting numbers itself.
    analysis = gemini.analyze_report(payload.report_type, payload.data)
    return schemas.AnalyzeReportResponse(report_type=payload.report_type, analysis=analysis)
