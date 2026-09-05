# Pebble (Urban Furniture) - Backend

A simple FastAPI + SQLAlchemy + SQLite accounting backend built for a 24-hour hackathon.
Modular monolith — no microservices, no message queues, no extra layers.

## Tech stack

- Python 3.11+
- FastAPI
- SQLAlchemy (ORM)
- SQLite
- Pydantic
- JWT auth (python-jose + passlib/bcrypt)
- Gemini API (analysis only — never used to calculate figures)
- Uvicorn

## Setup

```bash
# 1. From the repository root, create and activate a virtual environment
python -m venv Backend/.venv
source Backend/.venv/bin/activate        # Windows: Backend\.venv\Scripts\activate

# 2. Install dependencies
pip install -r Backend/requirements.txt

# 3. Configure environment variables
cp Backend/.env.example Backend/.env
# then edit .env and set SECRET_KEY and GEMINI_API_KEY

# 4. Seed the database with sample data (creates tables + sample data)
python -m Backend.seed

# 5. Run the server
uvicorn Backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive Swagger docs: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

## Default login (created by seed.py)

```
email: admin@urbanfurniture.com
password: admin123
```

Use `POST /auth/login` to get a JWT, then send it as:

```
Authorization: Bearer <token>
```

on every other request.

## Project structure

```
backend/
├── main.py         # FastAPI app + all routes
├── database.py     # SQLAlchemy engine/session/Base
├── models.py       # ORM models
├── schemas.py      # Pydantic request/response schemas
├── accounting.py   # journal-entry posting logic (double-entry, must balance)
├── reports.py       # P&L, balance sheet, trial balance, stock, budget calculations
├── gemini.py        # Gemini API wrapper (analysis only, never calculates numbers)
├── auth.py          # password hashing + JWT
├── seed.py          # sample data loader
├── requirements.txt
├── .env.example
└── .env
```

## Accounting logic implemented

- **Sale**: Debit Accounts Receivable (total) / Credit Sales Revenue (subtotal) / Credit Tax Payable (tax)
- **Purchase**: Debit Purchase Expense (total) / Credit Accounts Payable (total)
- **Payment received (customer)**: Debit Cash/Bank / Credit Accounts Receivable
- **Payment made (vendor)**: Debit Accounts Payable / Credit Cash/Bank

Every journal entry is validated so `SUM(debit) == SUM(credit)` before it is committed;
unbalanced entries are rejected with HTTP 400. Sale/purchase creation and their
journal postings happen inside a single DB transaction (rolled back together on failure).

Payments are validated against the outstanding amount on the referenced sale/purchase
(or total outstanding for the contact) and rejected if they would overpay.

## Reports

All reports (`/reports/*`) are computed directly from `JournalEntry`/`JournalItem`
data (and `StockMovement`/`Budget` for stock and budget reports). Gemini
(`POST /ai/analyze-report`) is only ever given the already-calculated JSON figures
and asked to write a natural-language summary — it never computes any accounting numbers.

## Notes for frontend integration (React/Vite)

- CORS is open (`allow_origins=["*"]`) so any local dev server can call the API.
- All list endpoints return plain JSON arrays; all mutating endpoints return the created/updated object.
- Validation errors return HTTP 400 with a `{"detail": "..."}` body (FastAPI default),
  same shape as auth/not-found errors, so the frontend can handle them uniformly.
