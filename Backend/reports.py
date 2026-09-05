"""
All reports are computed directly from JournalEntry / JournalItem data
(and StockMovement / Budget for their respective reports).
No numbers are ever computed by the AI - Gemini only summarizes numbers
already calculated here.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func

import Backend.models as models


def _account_balances(db: Session, period_start=None, period_end=None):
    """Returns {account_id: (account, total_debit, total_credit)}"""
    query = (
        db.query(
            models.JournalItem.account_id,
            func.sum(models.JournalItem.debit).label("debit"),
            func.sum(models.JournalItem.credit).label("credit"),
        )
        .join(
            models.JournalEntry,
            models.JournalItem.journal_entry_id == models.JournalEntry.id,
        )
        .group_by(models.JournalItem.account_id)
    )
    if period_start is not None:
        query = query.filter(models.JournalEntry.date >= period_start)
    if period_end is not None:
        query = query.filter(models.JournalEntry.date <= period_end)
    rows = query.all()
    result = {}
    for account_id, debit, credit in rows:
        account = db.query(models.Account).filter(models.Account.id == account_id).first()
        result[account_id] = (account, debit or 0.0, credit or 0.0)
    return result


def profit_and_loss(db: Session) -> dict:
    balances = _account_balances(db)

    income_accounts = []
    expense_accounts = []
    total_income = 0.0
    total_expense = 0.0

    for account_id, (account, debit, credit) in balances.items():
        if account is None:
            continue
        if account.type == models.AccountType.INCOME:
            amount = round(credit - debit, 2)
            income_accounts.append({"account": account.name, "code": account.code, "amount": amount})
            total_income += amount
        elif account.type == models.AccountType.EXPENSE:
            amount = round(debit - credit, 2)
            expense_accounts.append({"account": account.name, "code": account.code, "amount": amount})
            total_expense += amount

    total_income = round(total_income, 2)
    total_expense = round(total_expense, 2)
    net_profit = round(total_income - total_expense, 2)

    return {
        "report_type": "profit_loss",
        "income": income_accounts,
        "expenses": expense_accounts,
        "total_income": total_income,
        "total_expenses": total_expense,
        "net_profit": net_profit,
    }


def balance_sheet(db: Session) -> dict:
    balances = _account_balances(db)

    assets, liabilities, capital = [], [], []
    total_assets = total_liabilities = total_capital = 0.0

    for account_id, (account, debit, credit) in balances.items():
        if account is None:
            continue
        if account.type == models.AccountType.ASSET:
            amount = round(debit - credit, 2)
            assets.append({"account": account.name, "code": account.code, "amount": amount})
            total_assets += amount
        elif account.type == models.AccountType.LIABILITY:
            amount = round(credit - debit, 2)
            liabilities.append({"account": account.name, "code": account.code, "amount": amount})
            total_liabilities += amount
        elif account.type == models.AccountType.CAPITAL:
            amount = round(credit - debit, 2)
            capital.append({"account": account.name, "code": account.code, "amount": amount})
            total_capital += amount

    # Net profit for the period rolls into capital (retained earnings) for the equation to hold
    pl = profit_and_loss(db)
    net_profit = pl["net_profit"]
    total_capital_with_profit = round(total_capital + net_profit, 2)

    total_assets = round(total_assets, 2)
    total_liabilities = round(total_liabilities, 2)

    is_balanced = round(total_assets - (total_liabilities + total_capital_with_profit), 2) == 0.0

    return {
        "report_type": "balance_sheet",
        "assets": assets,
        "liabilities": liabilities,
        "capital": capital,
        "net_profit_transferred_to_capital": net_profit,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_capital": total_capital_with_profit,
        "is_balanced": is_balanced,
    }


def trial_balance(db: Session) -> dict:
    balances = _account_balances(db)
    rows = []
    total_debit = 0.0
    total_credit = 0.0

    for account_id, (account, debit, credit) in balances.items():
        if account is None:
            continue
        debit = round(debit, 2)
        credit = round(credit, 2)
        rows.append({
            "account": account.name,
            "code": account.code,
            "type": account.type.value,
            "debit": debit,
            "credit": credit,
        })
        total_debit += debit
        total_credit += credit

    total_debit = round(total_debit, 2)
    total_credit = round(total_credit, 2)

    return {
        "report_type": "trial_balance",
        "rows": rows,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": total_debit == total_credit,
    }


def stock_report(db: Session) -> dict:
    products = db.query(models.Product).all()
    rows = []
    for product in products:
        purchased = (
            db.query(func.sum(models.StockMovement.quantity))
            .filter(
                models.StockMovement.product_id == product.id,
                models.StockMovement.type == models.StockMovementType.PURCHASE_IN,
            )
            .scalar() or 0.0
        )
        sold = (
            db.query(func.sum(models.StockMovement.quantity))
            .filter(
                models.StockMovement.product_id == product.id,
                models.StockMovement.type == models.StockMovementType.SALE_OUT,
            )
            .scalar() or 0.0
        )
        adjusted = (
            db.query(func.sum(models.StockMovement.quantity))
            .filter(
                models.StockMovement.product_id == product.id,
                models.StockMovement.type == models.StockMovementType.ADJUSTMENT,
            )
            .scalar() or 0.0
        )
        current_stock = round(purchased - sold + adjusted, 2)
        rows.append({
            "product_id": product.id,
            "product": product.name,
            "purchased": round(purchased, 2),
            "sold": round(sold, 2),
            "adjusted": round(adjusted, 2),
            "current_stock": current_stock,
        })

    return {"report_type": "stock", "products": rows}


def budget_report(db: Session) -> dict:
    budgets = db.query(models.Budget).all()
    rows = []

    for budget in budgets:
        analytic = budget.analytic_account

        # Actual = sum of journal items posted to the analytic account's linked
        # regular account type in the budget period. Since JournalItem doesn't
        # carry analytic_account_id directly in this simple schema, we compute
        # "actual" from Sales/Purchases whose product category matches by name
        # as a simple heuristic is out of scope -> instead we sum all income/expense
        # journal activity within the period for accounts of the same type as
        # the analytic account. This keeps the report meaningful without
        # over-engineering the schema.
        balances = _account_balances(db, budget.period_start, budget.period_end)
        actual_amount = 0.0
        for account_id, (account, debit, credit) in balances.items():
            if account is None:
                continue
            if analytic.type == models.AnalyticType.INCOME and account.type == models.AccountType.INCOME:
                actual_amount += (credit - debit)
            elif analytic.type == models.AnalyticType.EXPENSE and account.type == models.AccountType.EXPENSE:
                actual_amount += (debit - credit)

        actual_amount = round(actual_amount, 2)
        planned = round(budget.planned_amount, 2)
        variance = round(actual_amount - planned, 2)
        utilization_pct = round((actual_amount / planned) * 100, 2) if planned else 0.0

        rows.append({
            "budget_id": budget.id,
            "name": budget.name,
            "analytic_account": analytic.name,
            "period_start": str(budget.period_start),
            "period_end": str(budget.period_end),
            "responsible_person": budget.responsible_person,
            "planned_amount": planned,
            "actual_amount": actual_amount,
            "variance": variance,
            "utilization_percent": utilization_pct,
        })

    return {"report_type": "budget", "budgets": rows}
