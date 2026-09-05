# Urban Furniture Frontend

The web interface for the Urban Furniture Accounting System. It is a React 19, TypeScript, and Vite single-page application.

## What it does

- Authenticates users and keeps their access token in browser local storage
- Shows contacts, products, inventory, invoices, vendor bills, payments, and reports
- Sends create, update, and delete actions to the FastAPI backend
- Updates the current page after a successful API response

The frontend does not connect to SQLite directly. All business and accounting operations go through the backend API.

## Prerequisites

- Node.js 20 or later
- npm
- The backend running and reachable at `http://127.0.0.1:8000` (unless configured otherwise)

## Start the app

From this directory:

```powershell
npm install
npm run dev
```

Vite prints the local URL in the terminal, normally `http://localhost:5173`.

Before signing in, start the backend from the repository root:

```powershell
uvicorn Backend.main:app --reload --port 8000
```

For first-time setup, seed the database first:

```powershell
python -m Backend.seed
```

The seeded development login is `admin@urbanfurniture.com` / `admin123`.

## Available commands

| Command | Purpose |
| --- | --- |
| `npm run dev` | Starts the Vite development server with hot reload. |
| `npm run build` | Type-checks and produces a production build in `dist/`. |
| `npm run preview` | Serves the already-built production output locally. |

## API configuration

The API base URL is configured in [`api.ts`](api.ts):

```ts
const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';
```

To point the frontend at another backend, create a `.env.local` file inside `Frontend`:

```text
VITE_API_URL=http://your-server:8000
```

Restart Vite after changing environment variables. Variables beginning with `VITE_` are embedded in the browser build, so never put passwords, API keys, or other secrets in them.

## Request and authentication flow

```text
Login form
  -> POST /auth/login
  <- JWT access token
  -> token saved as urban_furniture_access_token in localStorage
  -> later requests include Authorization: Bearer <token>
```

On startup, the app requests the logged-in user plus contacts, products, stock, sales, purchases, and payments in parallel. If token validation fails, it removes the token and returns to the login page.

The `api` object in [`api.ts`](api.ts) is the single API client used by [`main.tsx`](main.tsx). It attaches JSON headers when sending a request body, adds the saved token, turns backend errors into `ApiError`, and parses JSON responses.

## Source layout

```text
Frontend/
├── api.ts          # API base URL, token handling, endpoint calls, TypeScript types
├── main.tsx        # React application and screens
├── styles.css       # Application styling
├── vite.config.ts   # Vite + React configuration
└── package.json     # Dependencies and scripts
```

For the full setup and backend/database information, see the [project README](../README.md).
