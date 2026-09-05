"""
Core accounting logic: builds JournalEntry + JournalItem rows for each
business transaction, and enforces that every entry balances
(sum(debit) == sum(credit)) before it is committed.
"""
from datetime import date as date_cls
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import Backend.models as models

# Standard chart-of-account codes used by the automatic postings.
# These match the codes created by seed.py.
CODE_CASH = "1000"
CODE_BANK = "1100"
CODE_ACCOUNTS_RECEIVABLE = "1200"
CODE_INVENTORY = "1300"
CODE_ACCOUNTS_PAYABLE = "2000"
CODE_TAX_PAYABLE = "2100"
CODE_OWNER_CAPITAL = "3000"
CODE_SALES_REVENUE = "4000"
CODE_PURCHASE_EXPENSE = "5000"
CODE_OTHER_EXPENSES = "5100"


def get_account_by_code(db: Session, code: str) -> models.Account:
    account = db.query(models.Account).filter(models.Account.code == code).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Required system account with code '{code}' is missing. Run seed.py.",
        )
    return account


def get_or_create_journal(db: Session, name: str, jtype: str) -> models.Journal:
    journal = db.query(models.Journal).filter(models.Journal.name == name).first()
    if not journal:
        journal = models.Journal(name=name, type=jtype)
        db.add(journal)
        db.flush()
    return journal


def create_balanced_entry(
    db: Session,
    journal_id: int,
    lines: list,  # list of (account_id, debit, credit)
    reference: str = None,
    description: str = None,
    entry_date: date_cls = None,
) -> models.JournalEntry:
    """
    Creates a JournalEntry with JournalItems from `lines`.
    Rejects the entry (raises HTTPException 400) if debits != credits.
    Does NOT commit - caller controls the transaction boundary.
    """
    total_debit = round(sum(l[1] for l in lines), 2)
    total_credit = round(sum(l[2] for l in lines), 2)

    if total_debit != total_credit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unbalanced journal entry: total debit ({total_debit}) "
                f"!= total credit ({total_credit})"
            ),
        )

    entry = models.JournalEntry(
        journal_id=journal_id,
        date=entry_date or date_cls.today(),
        reference=reference,
        description=description,
    )
    db.add(entry)
    db.flush()  # get entry.id

    for account_id, debit, credit in lines:
        item = models.JournalItem(
            journal_entry_id=entry.id,
            account_id=account_id,
            debit=round(debit, 2),
            credit=round(credit, 2),
        )
        db.add(item)

    db.flush()
    return entry


def post_sale_entry(db: Session, sale: models.Sale) -> models.JournalEntry:
    """
    Debit: Accounts Receivable = total
    Credit: Sales Revenue = (total - tax)
    Credit: Tax Payable = tax
    """
    ar = get_account_by_code(db, CODE_ACCOUNTS_RECEIVABLE)
    revenue = get_account_by_code(db, CODE_SALES_REVENUE)
    tax_payable = get_account_by_code(db, CODE_TAX_PAYABLE)
    journal = get_or_create_journal(db, "Sales Journal", "SALES")

    base_amount = round(sale.total - sale.tax, 2)

    lines = [(ar.id, sale.total, 0.0), (revenue.id, 0.0, base_amount)]
    if sale.tax > 0:
        lines.append((tax_payable.id, 0.0, sale.tax))

    return create_balanced_entry(
        db,
        journal_id=journal.id,
        lines=lines,
        reference=f"SALE-{sale.id}",
        description=f"Sale #{sale.id} to contact {sale.customer_id}",
        entry_date=sale.date,
    )


def post_purchase_entry(db: Session, purchase: models.Purchase) -> models.JournalEntry:
    """
    Debit: Purchase Expense = total
    Credit: Accounts Payable = total
    """
    expense = get_account_by_code(db, CODE_PURCHASE_EXPENSE)
    ap = get_account_by_code(db, CODE_ACCOUNTS_PAYABLE)
    journal = get_or_create_journal(db, "Purchase Journal", "PURCHASE")

    lines = [(expense.id, purchase.total, 0.0), (ap.id, 0.0, purchase.total)]

    return create_balanced_entry(
        db,
        journal_id=journal.id,
        lines=lines,
        reference=f"PURCHASE-{purchase.id}",
        description=f"Purchase #{purchase.id} from contact {purchase.vendor_id}",
        entry_date=purchase.date,
    )


def post_payment_entry(db: Session, payment: models.Payment) -> models.JournalEntry:
    """
    Customer payment received (RECEIVE):
        Debit: Cash/Bank = amount
        Credit: Accounts Receivable = amount

    Vendor payment made (PAY):
        Debit: Accounts Payable = amount
        Credit: Cash/Bank = amount
    """
    cash_or_bank_code = CODE_BANK if payment.method == models.PaymentMethod.BANK else CODE_CASH
    cash_or_bank = get_account_by_code(db, cash_or_bank_code)
    journal = get_or_create_journal(
        db, "Bank Journal" if payment.method == models.PaymentMethod.BANK else "Cash Journal",
        "BANK" if payment.method == models.PaymentMethod.BANK else "CASH",
    )

    if payment.type == models.PaymentType.RECEIVE:
        ar = get_account_by_code(db, CODE_ACCOUNTS_RECEIVABLE)
        lines = [(cash_or_bank.id, payment.amount, 0.0), (ar.id, 0.0, payment.amount)]
        description = f"Payment received from contact {payment.contact_id}"
    else:
        ap = get_account_by_code(db, CODE_ACCOUNTS_PAYABLE)
        lines = [(ap.id, payment.amount, 0.0), (cash_or_bank.id, 0.0, payment.amount)]
        description = f"Payment made to contact {payment.contact_id}"

    return create_balanced_entry(
        db,
        journal_id=journal.id,
        lines=lines,
        reference=f"PAYMENT-{payment.id}",
        description=description,
        entry_date=payment.date,
    )


# ---------- Outstanding balance helpers (used to validate payments) ----------

def get_sale_outstanding(db: Session, sale: models.Sale) -> float:
    paid = (
        db.query(models.Payment)
        .filter(
            models.Payment.reference_id == sale.id,
            models.Payment.type == models.PaymentType.RECEIVE,
            models.Payment.contact_id == sale.customer_id,
        )
        .all()
    )
    total_paid = sum(p.amount for p in paid)
    return round(sale.total - total_paid, 2)


def get_purchase_outstanding(db: Session, purchase: models.Purchase) -> float:
    paid = (
        db.query(models.Payment)
        .filter(
            models.Payment.reference_id == purchase.id,
            models.Payment.type == models.PaymentType.PAY,
            models.Payment.contact_id == purchase.vendor_id,
        )
        .all()
    )
    total_paid = sum(p.amount for p in paid)
    return round(purchase.total - total_paid, 2)


def get_contact_outstanding(db: Session, contact_id: int, contact_type_is_customer: bool) -> float:
    """Total outstanding across all sales (if customer) or purchases (if vendor) for a contact."""
    if contact_type_is_customer:
        sales = db.query(models.Sale).filter(models.Sale.customer_id == contact_id).all()
        return round(sum(get_sale_outstanding(db, s) for s in sales), 2)
    else:
        purchases = db.query(models.Purchase).filter(models.Purchase.vendor_id == contact_id).all()
        return round(sum(get_purchase_outstanding(db, p) for p in purchases), 2)


def get_product_stock(db: Session, product_id: int) -> float:
    """Return the current on-hand quantity for one product."""
    purchased = sum(
        movement.quantity
        for movement in db.query(models.StockMovement)
        .filter(
            models.StockMovement.product_id == product_id,
            models.StockMovement.type == models.StockMovementType.PURCHASE_IN,
        )
        .all()
    )
    sold = sum(
        movement.quantity
        for movement in db.query(models.StockMovement)
        .filter(
            models.StockMovement.product_id == product_id,
            models.StockMovement.type == models.StockMovementType.SALE_OUT,
        )
        .all()
    )
    adjusted = sum(
        movement.quantity
        for movement in db.query(models.StockMovement)
        .filter(
            models.StockMovement.product_id == product_id,
            models.StockMovement.type == models.StockMovementType.ADJUSTMENT,
        )
        .all()
    )
    return round(purchased - sold + adjusted, 2)
