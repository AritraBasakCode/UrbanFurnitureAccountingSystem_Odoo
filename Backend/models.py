import enum
from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, Date, Enum, Text
)
from sqlalchemy.orm import relationship

from Backend.database import Base


# ---------- Enums ----------

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    ACCOUNTANT = "ACCOUNTANT"
    CONTACT = "CONTACT"


class ContactType(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    VENDOR = "VENDOR"
    BOTH = "BOTH"


class ProductType(str, enum.Enum):
    GOODS = "GOODS"
    SERVICE = "SERVICE"
    COMBO = "COMBO"


class AccountType(str, enum.Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    CAPITAL = "CAPITAL"


class TxnStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class PaymentType(str, enum.Enum):
    RECEIVE = "RECEIVE"
    PAY = "PAY"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    BANK = "BANK"


class AnalyticType(str, enum.Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class StockMovementType(str, enum.Enum):
    PURCHASE_IN = "PURCHASE_IN"
    SALE_OUT = "SALE_OUT"
    ADJUSTMENT = "ADJUSTMENT"


# ---------- Models ----------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.ACCOUNTANT, nullable=False)


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(ContactType), nullable=False)
    email = Column(String, nullable=True)
    mobile = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)

    sales = relationship("Sale", back_populates="customer")
    purchases = relationship("Purchase", back_populates="vendor")
    payments = relationship("Payment", back_populates="contact")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(ProductType), nullable=False)
    sales_price = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    category = relationship("Category", back_populates="products")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    type = Column(Enum(AccountType), nullable=False)


class Journal(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    default_debit_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    default_credit_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    tax = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False)
    date = Column(Date, default=date.today)
    status = Column(Enum(TxnStatus), default=TxnStatus.CONFIRMED)

    customer = relationship("Contact", back_populates="sales")
    product = relationship("Product")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    tax = Column(Float, nullable=False, default=0)
    total = Column(Float, nullable=False)
    date = Column(Date, default=date.today)
    status = Column(Enum(TxnStatus), default=TxnStatus.CONFIRMED)

    vendor = relationship("Contact", back_populates="purchases")
    product = relationship("Product")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)
    reference_id = Column(Integer, nullable=True)  # id of Sale or Purchase being settled
    type = Column(Enum(PaymentType), nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, default=date.today)

    contact = relationship("Contact", back_populates="payments")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    journal_id = Column(Integer, ForeignKey("journals.id"), nullable=False)
    date = Column(Date, default=date.today)
    reference = Column(String, nullable=True)
    description = Column(String, nullable=True)

    items = relationship("JournalItem", back_populates="entry", cascade="all, delete-orphan")


class JournalItem(Base):
    __tablename__ = "journal_items"

    id = Column(Integer, primary_key=True, index=True)
    journal_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    debit = Column(Float, nullable=False, default=0)
    credit = Column(Float, nullable=False, default=0)

    entry = relationship("JournalEntry", back_populates="items")
    account = relationship("Account")


class AnalyticAccount(Base):
    __tablename__ = "analytic_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(AnalyticType), nullable=False)

    budgets = relationship("Budget", back_populates="analytic_account")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    responsible_person = Column(String, nullable=True)
    analytic_account_id = Column(Integer, ForeignKey("analytic_accounts.id"), nullable=False)
    planned_amount = Column(Float, nullable=False)

    analytic_account = relationship("AnalyticAccount", back_populates="budgets")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    type = Column(Enum(StockMovementType), nullable=False)
    quantity = Column(Float, nullable=False)
    reference_id = Column(Integer, nullable=True)
    date = Column(Date, default=date.today)

    product = relationship("Product")
