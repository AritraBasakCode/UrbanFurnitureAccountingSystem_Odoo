"""
Run this once after setting up the database to populate sample data:

    python seed.py
"""
from Backend.database import SessionLocal, init_db
from Backend.auth import hash_password
import Backend.models as models


def seed():
    init_db()
    db = SessionLocal()

    try:
        # ---------- Admin user ----------
        if not db.query(models.User).filter(models.User.email == "admin@urbanfurniture.com").first():
            admin = models.User(
                name="Admin User",
                email="admin@urbanfurniture.com",
                password_hash=hash_password("admin123"),
                role=models.UserRole.ADMIN,
            )
            db.add(admin)
            print("Created admin user: admin@urbanfurniture.com / admin123")

        # ---------- Contacts ----------
        contacts_data = [
            {"name": "Nimesh Pathak", "type": models.ContactType.CUSTOMER, "email": "nimesh@example.com",
             "mobile": "9876543210", "address": "12 MG Road", "city": "Ahmedabad", "state": "Gujarat", "pincode": "380001"},
            {"name": "Azure Furniture", "type": models.ContactType.VENDOR, "email": "sales@azurefurniture.com",
             "mobile": "9123456780", "address": "45 Industrial Area", "city": "Surat", "state": "Gujarat", "pincode": "395001"},
        ]
        for c in contacts_data:
            if not db.query(models.Contact).filter(models.Contact.name == c["name"]).first():
                db.add(models.Contact(**c))

        # ---------- Category ----------
        category_name = "Furniture"
        category = db.query(models.Category).filter(models.Category.name == category_name).first()
        if not category:
            category = models.Category(name=category_name)
            db.add(category)
            db.flush()

        # ---------- Products ----------
        products_data = [
            {"name": "Office Chair", "type": models.ProductType.GOODS, "sales_price": 4500, "purchase_price": 3000},
            {"name": "Wooden Table", "type": models.ProductType.GOODS, "sales_price": 12000, "purchase_price": 8000},
            {"name": "Sofa", "type": models.ProductType.GOODS, "sales_price": 25000, "purchase_price": 18000},
            {"name": "Dining Table", "type": models.ProductType.GOODS, "sales_price": 20000, "purchase_price": 14000},
        ]
        for p in products_data:
            if not db.query(models.Product).filter(models.Product.name == p["name"]).first():
                db.add(models.Product(**p, category_id=category.id))

        # ---------- Accounts ----------
        accounts_data = [
            {"code": "1000", "name": "Cash", "type": models.AccountType.ASSET},
            {"code": "1100", "name": "Bank", "type": models.AccountType.ASSET},
            {"code": "1200", "name": "Accounts Receivable", "type": models.AccountType.ASSET},
            {"code": "1300", "name": "Inventory", "type": models.AccountType.ASSET},
            {"code": "2000", "name": "Accounts Payable", "type": models.AccountType.LIABILITY},
            {"code": "2100", "name": "Tax Payable", "type": models.AccountType.LIABILITY},
            {"code": "3000", "name": "Owner Capital", "type": models.AccountType.CAPITAL},
            {"code": "4000", "name": "Sales Revenue", "type": models.AccountType.INCOME},
            {"code": "5000", "name": "Purchase Expense", "type": models.AccountType.EXPENSE},
            {"code": "5100", "name": "Other Expenses", "type": models.AccountType.EXPENSE},
        ]
        for a in accounts_data:
            if not db.query(models.Account).filter(models.Account.code == a["code"]).first():
                db.add(models.Account(**a))

        db.flush()

        # ---------- Journals ----------
        ar = db.query(models.Account).filter(models.Account.code == "1200").first()
        revenue = db.query(models.Account).filter(models.Account.code == "4000").first()
        expense = db.query(models.Account).filter(models.Account.code == "5000").first()
        ap = db.query(models.Account).filter(models.Account.code == "2000").first()
        cash = db.query(models.Account).filter(models.Account.code == "1000").first()
        bank = db.query(models.Account).filter(models.Account.code == "1100").first()

        journals_data = [
            {"name": "Sales Journal", "type": "SALES", "default_debit_account_id": ar.id, "default_credit_account_id": revenue.id},
            {"name": "Purchase Journal", "type": "PURCHASE", "default_debit_account_id": expense.id, "default_credit_account_id": ap.id},
            {"name": "Cash Journal", "type": "CASH", "default_debit_account_id": cash.id, "default_credit_account_id": cash.id},
            {"name": "Bank Journal", "type": "BANK", "default_debit_account_id": bank.id, "default_credit_account_id": bank.id}
        ]
        for j in journals_data:
            if not db.query(models.Journal).filter(models.Journal.name == j["name"]).first():
                db.add(models.Journal(**j))

        db.commit()
        print("Seed data inserted successfully.")
    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
