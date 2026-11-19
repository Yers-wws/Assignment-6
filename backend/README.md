# Voltix TechStore — REST API Backend

A fully functional REST API backend for the **Voltix TechStore** electronics e-commerce application, built with **Python**, **FastAPI**, and **Pydantic** as part of the CSS 225 Web Programming Fundamentals course (Weeks 9–11).

---

## Project Architecture

The project follows a layered architecture with clear separation of concerns:

```text
backend/
├── main.py                  # Application entry point, FastAPI init, CORS middleware, router registration
├── config.py                # Configuration constants (shipping thresholds, promo codes)
├── requirements.txt         # Project dependencies
├── models/
│   ├── __init__.py
│   └── schemas.py           # Pydantic schemas for strict request/response validation
├── routers/
│   ├── __init__.py
│   ├── products.py          # Product catalog and review endpoints (/api/products)
│   ├── orders.py            # Order checkout and cancellation endpoints (/api/orders)
│   └── promos.py            # Promo code validation endpoints (/api/promos)
├── services/
│   ├── __init__.py
│   ├── product_service.py   # Business logic: catalog filtering, price calculation, rating aggregation
│   ├── order_service.py     # Business logic: stock reservation, discount application, order cancellation
│   └── promo_service.py     # Business logic: promo code validation
├── storage/
│   ├── __init__.py
│   └── db.py                # Thread-safe in-memory database with realistic seed data
└── tests/
    ├── __init__.py
    └── test_api.py          # Automated test suite (pytest + TestClient, 27 tests)
```

---

## Core Workflows

### 1. Product Catalog & Inventory Management
* **Browse & Filter:** filter by category (`category`), brand (`brand`), price range (`min_price`, `max_price`), stock availability (`in_stock`), full-text search (`search`), and sorting (`sort_by`: price_asc, price_desc, rating, discount, name).
* **Detailed View:** retrieve a single product with automatically calculated discounted sale price (`sale_price`) and dynamically aggregated average rating.
* **Full CRUD:** create new products, partially update fields and inventory stock (`PATCH` with `exclude_unset=True`), and delete products (`DELETE` returning `204 No Content`).

### 2. Order Checkout & Stock Reservation
* **Multi-resource interaction:** Products ↔ Orders ↔ Promotions.
* **Validation:**
  * Email format validation via regex.
  * Product existence check (returns `404 Not Found` if the product does not exist).
  * Stock availability check — if the requested quantity exceeds available stock, the order is rejected with `400 Bad Request` ("Insufficient stock for '{title}'. Requested: X, Available: Y").
* **Business Logic:**
  * Promo code application (`TECH10` = 10% off). Invalid codes are rejected with `400 Bad Request`.
  * Shipping fee calculation: orders totaling $500 or more qualify for **free shipping**; otherwise, a flat $15 fee applies.
  * **Atomic stock deduction:** purchased quantities are immediately subtracted from inventory within a thread-safe lock.
* **Order Cancellation (`POST /api/orders/{id}/cancel`):**
  * Sets order status to `cancelled`.
  * **Automatically restores reserved stock** back to inventory.
  * Attempting to cancel an already-cancelled order returns `400 Bad Request`.

### 3. Customer Reviews & Dynamic Rating Recalculation
* Customers can submit reviews with star ratings (1–5) and text comments.
* Upon review submission, the backend automatically recalculates the product's average rating (`rating`) and increments the review count (`reviews_count`).

### 4. Promotions & Discounts
* `POST /api/promos/validate` — validate a promo code and preview the discount amount before completing checkout.
* `GET /api/promos` — list all currently active promotional codes.

---

## REST API Specification

| Method | Endpoint | Status Codes | Description |
| :--- | :--- | :--- | :--- |
| **GET** | `/health` | `200 OK` | Health check |
| **GET** | `/api/categories` | `200 OK` | List supported product categories |
| **GET** | `/api/products` | `200 OK` | List products with filtering, search, and sorting |
| **GET** | `/api/products/{id}` | `200 OK` / `404` | Get product details by ID |
| **POST** | `/api/products` | `201 Created` / `422` | Add a new product to the catalog |
| **PATCH** | `/api/products/{id}` | `200 OK` / `404` | Partially update product fields or stock |
| **DELETE** | `/api/products/{id}` | `204 No Content` / `404` | Remove a product from the catalog |
| **GET** | `/api/products/{id}/reviews` | `200 OK` / `404` | List all reviews for a product |
| **POST** | `/api/products/{id}/reviews` | `201 Created` / `422` | Submit a review (triggers rating recalculation) |
| **GET** | `/api/orders` | `200 OK` | List all placed orders |
| **POST** | `/api/orders` | `201 Created` / `400` / `404` / `422` | Place an order with stock deduction |
| **GET** | `/api/orders/{id}` | `200 OK` / `404` | Get order details by ID |
| **POST** | `/api/orders/{id}/cancel` | `200 OK` / `400` / `404` | Cancel an order and restore stock |
| **POST** | `/api/promos/validate` | `200 OK` / `400` | Validate a promo code |
| **GET** | `/api/promos` | `200 OK` | List active promotional codes |

---

## Getting Started

### 1. Activate the Virtual Environment

From the `backend/` directory in PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Start the Development Server
```powershell
python main.py
# or
uvicorn main:app --reload --port 8000
```
The server will be available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 4. Interactive API Documentation (Swagger UI)

Open in your browser:
* **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Running Automated Tests

Run the full test suite with verbose output:
```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

The test suite includes **27 test cases** covering:
* Successful operations (`200 OK`, `201 Created`, `204 No Content`)
* Validation errors (`422 Unprocessable Entity`)
* Business rule violations (`400 Bad Request`)
* Resource not found (`404 Not Found`)
* Complete test isolation via automatic database reset before each test

---

## Tech Stack

| Component | Technology |
| :--- | :--- |
| Language | Python 3.12 |
| Web Framework | FastAPI |
| Data Validation | Pydantic v2 |
| ASGI Server | Uvicorn |
| Testing | pytest + TestClient |
| Data Storage | Thread-safe In-Memory (dict + threading.Lock) |
| API Documentation | Auto-generated Swagger UI / ReDoc |
