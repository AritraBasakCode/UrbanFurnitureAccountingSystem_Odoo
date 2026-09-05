# Urban Furniture Accounting System

A full-stack accounting application for a furniture business. It provides master-data management, sales and purchase transactions, payments, stock visibility, double-entry journal posting, and financial reports.

## Architecture

```text
React + Vite frontend (browser)
        |
        | JSON over HTTP
        v
FastAPI backend (port 8000)
        |
        | SQLAlchemy ORM
        v
SQLite database (urban_furniture.db)
```

The frontend does not access the database directly. It calls the authenticated FastAPI API, which applies validation and accounting rules before reading or writing data.

## Features

- Role-based login for administrators, accountants, and contacts
- Contact, product, category, account, and journal management
- Sales invoices, vendor bills, and customer/vendor payments
- Automatic, balanced double-entry journal entries for transactions
- Stock movements and stock-on-hand reporting
- Profit and loss, balance sheet, trial balance, and budget reporting
- Optional Gemini-powered natural-language report analysis

## Prerequisites

- Python 3.11 or later
- Node.js 20 or later (includes npm)

## Run locally

Open two terminals at the repository root.

### 1. Configure and start the backend

```powershell
python -m venv Backend/.venv
Backend\.venv\Scripts\Activate.ps1
pip install -r Backend/requirements.txt
Copy-Item Backend/.env.example Backend/.env
python -m Backend.seed
uvicorn Backend.main:app --reload --port 8000
```

Edit `Backend/.env` before production use. At minimum, replace `SECRET_KEY`; add `GEMINI_API_KEY` only if you use AI report analysis.

The API is available at <http://127.0.0.1:8000>, with interactive documentation at <http://127.0.0.1:8000/docs>.

### 2. Start the frontend

```powershell
Set-Location Frontend
npm install
npm run dev
```

Open the Vite URL printed in the terminal (normally <http://localhost:5173>).

The seed command creates a development administrator account:

```text
Email:    admin@urbanfurniture.com
Password: admin123
```

Change or remove this account before any real deployment.

## Database

By default, data is stored locally in [`urban_furniture.db`](urban_furniture.db), a SQLite database file. The connection URL is configured by `DATABASE_URL` in `Backend/.env` and defaults to `sqlite:///./urban_furniture.db`.

Because this is a relative path, start the backend from the repository root as shown above to use the root database file. You can inspect it with DB Browser for SQLite or a VS Code SQLite extension. Avoid manually editing financial records while the app is running, since that bypasses application validation and journal posting.

## Project layout

```text
.
├── Backend/                 # FastAPI API, models, accounting rules, reports
├── Frontend/                # React + TypeScript + Vite web application
├── urban_furniture.db       # Local SQLite database (created/updated at runtime)
└── README.md                # This guide
```

See [Backend/README.md](Backend/README.md) for backend-specific API and accounting details, and [Frontend/README.md](Frontend/README.md) for frontend setup and configuration.
