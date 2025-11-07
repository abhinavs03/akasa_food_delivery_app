# Akasa Food Ordering Platform

Python FastAPI app with SQLite, server-rendered UI, and JWT auth.

## Features
- Registration/Login (hashed passwords, JWT; cookie stored)
- Browse inventory by category
- Persistent cart per user across devices
- Checkout with stock validation and order creation
- Order history and order status (simple lifecycle: PLACED)
- Security basics: input validation via Pydantic/FastAPI, CORS middleware

## Tech Stack
- FastAPI, SQLModel, SQLite
- Jinja2 templates for UI
- passlib (bcrypt), python-jose (JWT)

## Getting Started

### 1) Install dependencies
```bash
python -m venv .venv
. .venv/Scripts/activate  # on Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2) Seed the database
```bash
python scripts/seed.py
```
(Or use `python -m scripts.seed` if the above doesn't work)

### 3) Run the server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Important:** After starting the server, open `http://localhost:8000` or `http://127.0.0.1:8000` in your browser. 
Do NOT use `http://0.0.0.0:8000` - that's just the server bind address, not a valid URL.

## Usage
- Register a user via `Auth → Register`
- Login via `Auth → Login` (token stored in cookie)
- Browse `Browse` and add to cart
- Open `Cart` to update quantities or remove
- Click `Pay and Proceed` to checkout
- View `Orders` for history and status

## Environment Variables
- `DATABASE_URL` (default: sqlite:///./data.db)
- `SECRET_KEY` (set a strong random value in production)

## Deployment (Render/Railway)
- Create a new Web Service from GitHub repo
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set env vars: `SECRET_KEY`, optionally `DATABASE_URL`

## Next Improvements
- Pagination and search for items
- Payment gateway integration and real statuses (SHIPPED/DELIVERED)
- Admin dashboard to manage inventory and orders
- Rate limiting and CSRF protection for form posts
- Email notifications
