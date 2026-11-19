"""Comprehensive automated test suite for Voltix TechStore API.

Covers:
- Database isolation via in-memory SQLite and dependency overrides.
- Workflow 1: Catalog browsing, filtering, CRUD operations.
- Workflow 2: Customer reviews, rating recalculation in DB.
- Workflow 3: Order checkout with transactional stock deduction, cancellation & restoration.
- Workflow 4: Promo code validation and discount calculations.
- Edge cases: 400 Bad Request (insufficient stock, duplicate cancel), 404 Not Found, 409 Conflict (deleting product in order), 422 Validation Error, 204 No Content.
- Transaction integrity: order failure triggers complete rollback.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db
from models.orm import Product, Order, OrderItem
from scripts.seed import seed_database

# Isolated in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_database():
    """Arrange: reset and re-seed the test database before each test for complete test isolation."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    seed_database(target_engine=test_engine, session_factory=TestingSessionLocal)
    yield


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# System & Meta Tests
# =====================================================================
def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "documentation" in data
    assert data["documentation"] == "/docs"


# =====================================================================
# Workflow 1: Catalog & Products Tests
# =====================================================================
def test_list_products(client):
    res = client.get("/api/products")
    assert res.status_code == 200
    products = res.json()
    assert len(products) > 0
    # Check fields present
    first = products[0]
    assert "id" in first
    assert "title" in first
    assert "price" in first
    assert "sale_price" in first
    assert "stock" in first


def test_filter_products_by_category(client):
    res = client.get("/api/products?category=smartphones")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 2
    assert all(p["category"] == "smartphones" for p in items)


def test_search_products(client):
    res = client.get("/api/products?search=macbook")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    assert any("macbook" in p["title"].lower() for p in items)


def test_filter_products_in_stock(client):
    res = client.get("/api/products?in_stock=true")
    assert res.status_code == 200
    items = res.json()
    assert all(p["stock"] > 0 for p in items)


def test_sort_products_price_asc(client):
    res = client.get("/api/products?sort_by=price_asc")
    assert res.status_code == 200
    items = res.json()
    prices = [p["sale_price"] for p in items]
    assert prices == sorted(prices)


def test_get_single_product_success(client):
    res = client.get("/api/products/1")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == 1
    assert data["title"] == "iPhone 15 Pro"


def test_get_single_product_not_found(client):
    res = client.get("/api/products/9999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_create_product_success(client):
    new_item = {
        "title": "Sony WH-1000XM5",
        "description": "Industry Leading Wireless Noise Cancelling Headphones",
        "category": "mobile-accessories",
        "price": 399.99,
        "discount_percentage": 10.0,
        "stock": 25,
        "brand": "Sony",
        "thumbnail": "https://via.placeholder.com/300",
        "images": []
    }
    res = client.post("/api/products", json=new_item)
    assert res.status_code == 201
    created = res.json()
    assert created["id"] > 0
    assert created["title"] == "Sony WH-1000XM5"
    assert created["sale_price"] == round(399.99 * 0.9, 2)

    # Verify presence in list
    check = client.get(f"/api/products/{created['id']}")
    assert check.status_code == 200


def test_create_product_validation_error(client):
    # Invalid: price is 0 or negative
    bad_item = {
        "title": "Bad Product",
        "description": "Short",
        "category": "smartphones",
        "price": -10.0,
        "stock": 5,
        "brand": "Test"
    }
    res = client.post("/api/products", json=bad_item)
    assert res.status_code == 422


def test_update_product_partial(client):
    update_data = {"price": 1050.00, "stock": 50}
    res = client.patch("/api/products/1", json=update_data)
    assert res.status_code == 200
    updated = res.json()
    assert updated["price"] == 1050.00
    assert updated["stock"] == 50
    # Original title remains unchanged
    assert updated["title"] == "iPhone 15 Pro"


def test_update_product_not_found(client):
    res = client.patch("/api/products/9999", json={"stock": 10})
    assert res.status_code == 404


def test_delete_product_success(client):
    # 204 No Content
    res = client.delete("/api/products/1")
    assert res.status_code == 204

    # Subsequent GET returns 404
    res2 = client.get("/api/products/1")
    assert res2.status_code == 404


def test_delete_product_not_found(client):
    res = client.delete("/api/products/9999")
    assert res.status_code == 404


# =====================================================================
# Workflow 2: Reviews and Ratings Tests
# =====================================================================
def test_add_review_recalculates_rating(client):
    # iPhone 15 Pro (id=1) initially has 1 review with rating 5.0
    new_review = {
        "reviewer_name": "Maria Garcia",
        "rating": 3,
        "comment": "Good phone but a bit warm during gaming."
    }
    res = client.post("/api/products/1/reviews", json=new_review)
    assert res.status_code == 201
    created_rev = res.json()
    assert created_rev["rating"] == 3
    assert created_rev["reviewer_name"] == "Maria Garcia"

    # Fetch product to verify average rating recalculation: (5 + 3) / 2 = 4.0
    p_res = client.get("/api/products/1")
    product = p_res.json()
    assert product["rating"] == 4.0
    assert product["reviews_count"] == 2


def test_add_review_validation_error(client):
    # Rating > 5 is invalid
    bad_review = {
        "reviewer_name": "John",
        "rating": 6,
        "comment": "Super"
    }
    res = client.post("/api/products/1/reviews", json=bad_review)
    assert res.status_code == 422


def test_add_review_product_not_found(client):
    review = {
        "reviewer_name": "John Doe",
        "rating": 5,
        "comment": "Nice gadget!"
    }
    res = client.post("/api/products/9999/reviews", json=review)
    assert res.status_code == 404


# =====================================================================
# Workflow 3: Orders, Inventory Reservation & Cancellation Tests
# =====================================================================
def test_order_checkout_success_with_promo(client):
    # Check initial stock of iPhone 15 Pro (id 1) = 15
    initial_p = client.get("/api/products/1").json()
    initial_stock = initial_p["stock"]

    order_payload = {
        "customer_name": "Yersultan Temir",
        "email": "yersultan@example.com",
        "shipping_address": "Kabanbay Batyr 53, Astana",
        "items": [
            {"product_id": 1, "quantity": 2}
        ],
        "promo_code": "TECH10"
    }
    res = client.post("/api/orders", json=order_payload)
    assert res.status_code == 201
    order = res.json()

    assert order["id"] >= 1001
    assert order["customer_name"] == "Yersultan Temir"
    assert order["email"] == "yersultan@example.com"
    assert order["status"] == "confirmed"
    assert order["promo_code"] == "TECH10"

    # Math verification:
    # iPhone 15 Pro price 999 with 5% discount = 949.05 each
    # 2 items = 1898.10 subtotal
    # Promo TECH10 (10% off) = 189.81 discount
    # Subtotal after discount = 1708.29 >= 500 => free shipping ($0.0)
    assert order["discount"] > 0
    assert order["shipping"] == 0.0
    assert order["total"] == round(order["subtotal"] - order["discount"], 2)

    # Verify inventory was atomically deducted
    updated_p = client.get("/api/products/1").json()
    assert updated_p["stock"] == initial_stock - 2


def test_order_checkout_insufficient_stock_fails(client):
    # Try to order 20 units when only 15 available
    order_payload = {
        "customer_name": "Buyer",
        "email": "buyer@example.com",
        "shipping_address": "Main Street 12, Almaty",
        "items": [
            {"product_id": 1, "quantity": 20}
        ]
    }
    res = client.post("/api/orders", json=order_payload)
    assert res.status_code == 400
    assert "insufficient stock" in res.json()["detail"].lower()


def test_order_checkout_invalid_promo_fails(client):
    order_payload = {
        "customer_name": "Buyer",
        "email": "buyer@example.com",
        "shipping_address": "Main Street 12, Almaty",
        "items": [
            {"product_id": 1, "quantity": 1}
        ],
        "promo_code": "NOT_A_REAL_CODE"
    }
    res = client.post("/api/orders", json=order_payload)
    assert res.status_code == 400
    assert "invalid" in res.json()["detail"].lower()


def test_order_checkout_invalid_email_fails(client):
    order_payload = {
        "customer_name": "Buyer",
        "email": "not-an-email",
        "shipping_address": "Main Street 12, Almaty",
        "items": [
            {"product_id": 1, "quantity": 1}
        ]
    }
    res = client.post("/api/orders", json=order_payload)
    assert res.status_code == 422


def test_order_cancellation_restores_stock(client):
    # Place order for 3 items
    initial_stock = client.get("/api/products/1").json()["stock"]

    order_payload = {
        "customer_name": "Test User",
        "email": "user@test.kz",
        "shipping_address": "Dostyk Ave 45",
        "items": [{"product_id": 1, "quantity": 3}]
    }
    order_res = client.post("/api/orders", json=order_payload)
    order_id = order_res.json()["id"]

    # Stock should be reduced
    assert client.get("/api/products/1").json()["stock"] == initial_stock - 3

    # Cancel the order
    cancel_res = client.post(f"/api/orders/{order_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Stock MUST be restored!
    assert client.get("/api/products/1").json()["stock"] == initial_stock

    # Cancelling again should return 400
    double_cancel = client.post(f"/api/orders/{order_id}/cancel")
    assert double_cancel.status_code == 400


# =====================================================================
# Workflow 4: Promo Code Service Tests
# =====================================================================
def test_promo_validation_valid(client):
    res = client.post("/api/promos/validate", json={"code": "TECH10", "subtotal": 200.0})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["discount_percentage"] == 10.0
    assert data["discount_amount"] == 20.0


def test_promo_validation_invalid(client):
    res = client.post("/api/promos/validate", json={"code": "FAKECAP", "subtotal": 100.0})
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert data["discount_amount"] == 0.0


# =====================================================================
# Frontend Compatibility Tests
# =====================================================================
def test_category_compatibility_endpoint(client):
    res = client.get("/api/products/category/smartphones")
    assert res.status_code == 200
    data = res.json()
    assert "products" in data
    assert len(data["products"]) >= 2


def test_cart_add_compatibility_endpoint(client):
    payload = {
        "userId": 1,
        "products": [{"id": 1, "quantity": 1}]
    }
    res = client.post("/api/carts/add", json=payload)
    assert res.status_code == 201
    assert res.json()["id"] >= 1001


# =====================================================================
# Database Specific Integrity Tests (Requirements 14, 16, 18, 21)
# =====================================================================
def test_delete_product_referenced_in_order_fails_409(client):
    """Requirement 14: cannot delete product that is referenced in existing orders (returns 409)."""
    # Create an order referencing product 1
    order_payload = {
        "customer_name": "Conflict Buyer",
        "email": "buyer@conflict.kz",
        "shipping_address": "Abylai Khan 10",
        "items": [{"product_id": 1, "quantity": 1}],
    }
    order_res = client.post("/api/orders", json=order_payload)
    assert order_res.status_code == 201

    # Attempt to delete product 1
    delete_res = client.delete("/api/products/1")
    assert delete_res.status_code == 409
    assert "order" in delete_res.json()["detail"].lower()


def test_order_transaction_rollback_on_failure(client):
    """Requirement 18: upon failure at any step of order, roll back entire transaction without partial stock deduction."""
    initial_stock_1 = client.get("/api/products/1").json()["stock"]
    initial_stock_2 = client.get("/api/products/2").json()["stock"]

    # Order item 1 (valid qty 2) and item 2 (qty 20 exceeding product 2 stock of 12)
    bad_order_payload = {
        "customer_name": "Rollback Tester",
        "email": "tester@rollback.com",
        "shipping_address": "Test Street 1",
        "items": [
            {"product_id": 1, "quantity": 2},
            {"product_id": 2, "quantity": 20},
        ],
    }
    res = client.post("/api/orders", json=bad_order_payload)
    assert res.status_code == 400

    # Verify item 1 stock was NOT deducted partially
    p1_stock = client.get("/api/products/1").json()["stock"]
    p2_stock = client.get("/api/products/2").json()["stock"]
    assert p1_stock == initial_stock_1
    assert p2_stock == initial_stock_2


def test_get_categories_from_database(client):
    """Requirement 12: GET /api/categories returns data from categories table."""
    # Dict format (default)
    res = client.get("/api/categories")
    assert res.status_code == 200
    data = res.json()
    assert "smartphones" in data
    assert "laptops" in data

    # List format
    res_list = client.get("/api/categories?format=list")
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert isinstance(data_list, list)
    assert any(c["slug"] == "smartphones" for c in data_list)


# =====================================================================
# Workflow 5: Product Advisor Recommendation Tests (Part 7)
# =====================================================================
def test_recommend_success(client):
    """Requirement 25: budget observed, top 3 sorted by score (0-100), reasons provided."""
    payload = {
        "category": "laptops",
        "budget": 2000.0,
        "use_case": "dev",
        "priority": "memory"
    }
    res = client.post("/api/recommend", json=payload)
    assert res.status_code == 200
    items = res.json()
    assert len(items) <= 3
    assert len(items) > 0

    # Budget constraint verification
    assert all(item["sale_price"] <= 2000.0 for item in items)

    # Score strictly normalized between 0 and 100
    assert all(0.0 <= item["score"] <= 100.0 for item in items)

    # Sorted by score descending
    scores = [item["score"] for item in items]
    assert scores == sorted(scores, reverse=True)

    # Reasons in Russian
    first = items[0]
    assert "score" in first
    assert "reasons" in first
    assert len(first["reasons"]) > 0
    assert any("бюджет" in r.lower() or "памят" in r.lower() or "наличи" in r.lower() for r in first["reasons"])


def test_recommend_invalid_category_returns_422(client):
    """Requirement 25: invalid category returns 422 Unprocessable Entity."""
    payload = {
        "category": "smartwatch",
        "budget": 500.0,
        "use_case": "daily",
        "priority": "battery"
    }
    res = client.post("/api/recommend", json=payload)
    assert res.status_code == 422


def test_recommend_invalid_priority_for_category_returns_422(client):
    """Requirement 3: camera is not a valid priority for laptops, must return 422."""
    payload = {
        "category": "laptops",
        "budget": 1500.0,
        "use_case": "office",
        "priority": "camera"
    }
    res = client.post("/api/recommend", json=payload)
    assert res.status_code == 422


def test_recommend_empty_result_returns_404_with_min_price_hint(client):
    """Requirement 7 & 25: budget too low returns 404 with helpful minimum price hint."""
    payload = {
        "category": "laptops",
        "budget": 50.0,
        "use_case": "gaming",
        "priority": "gpu"
    }
    res = client.post("/api/recommend", json=payload)
    assert res.status_code == 404
    detail = res.json()["detail"].lower()
    assert "минимальная цена" in detail or "бюджет" in detail


def test_recommend_invalid_budget_returns_422(client):
    """Requirement 24: budget <= 0 returns 422."""
    payload = {
        "category": "smartphones",
        "budget": -100.0,
        "use_case": "photo",
        "priority": "camera"
    }
    res = client.post("/api/recommend", json=payload)
    assert res.status_code == 422


def test_recommend_tablets_success(client):
    """Requirement 3 & 9: Advisor supports tablets category."""
    payload = {
        "category": "tablets",
        "budget": 1000.0,
        "use_case": "study",
        "priority": "battery"
    }
    res = client.post("/api/recommend", json=payload)
    assert res.status_code == 200
    items = res.json()
    assert len(items) > 0
    assert all(item["category"] == "tablets" for item in items)
    assert all(0.0 <= item["score"] <= 100.0 for item in items)


def test_catalog_has_actual_2025_2026_products(client):
    """Stage 2, Items 8-10: Catalog contains verified 2025-2026 flagship and mainstream devices."""
    res = client.get("/api/products?limit=100")
    assert res.status_code == 200
    products = res.json()
    assert len(products) >= 46

    titles = {p["title"] for p in products}

    # Verify at least 8 new smartphones are in the catalog
    new_phones = [
        "iPhone 16 Pro", "Samsung Galaxy S25 Ultra", "Google Pixel 9 Pro",
        "OnePlus 13", "Xiaomi 15", "ASUS ROG Phone 9 Pro",
        "Samsung Galaxy S24 FE", "iPhone 16"
    ]
    for phone in new_phones:
        assert phone in titles, f"Missing actual smartphone: {phone}"

    # Verify at least 8 new laptops
    new_laptops = [
        "MacBook Pro 14 (M4)", "Dell XPS 14 9440", "ASUS ROG Zephyrus G16 (2024)",
        "Lenovo ThinkPad X1 Carbon Gen 12", "Lenovo Legion Pro 7i Gen 9",
        "ASUS Zenbook S 14 (UX5406)", "HP OmniBook X 14", "Acer Swift 14 AI"
    ]
    for laptop in new_laptops:
        assert laptop in titles, f"Missing actual laptop: {laptop}"

    # Verify at least 4 new tablets
    new_tablets = [
        "iPad Pro 11 (M4)", "Samsung Galaxy Tab S10+",
        "iPad mini (A17 Pro)", "Xiaomi Pad 6S Pro 12.4"
    ]
    for tablet in new_tablets:
        assert tablet in titles, f"Missing actual tablet: {tablet}"

    # Verify accessories
    new_accessories = [
        "AirPods 4 with Active Noise Cancellation",
        "Samsung Galaxy Buds3 Pro",
        "Anker MagGo Power Bank 10000mAh"
    ]
    for acc in new_accessories:
        assert acc in titles, f"Missing actual accessory: {acc}"

    # Verify that products 1 and 2 remain unchanged
    p1 = client.get("/api/products/1").json()
    assert p1["title"] == "iPhone 15 Pro"
    p2 = client.get("/api/products/2").json()
    assert p2["title"] == "Samsung Galaxy S24 Ultra"


def test_advisor_recommends_new_tablets(client):
    """Stage 2: Advisor successfully recommends newly added tablet models with correct scoring."""
    payload = {
        "category": "tablets",
        "budget": 1200.0,
        "use_case": "work",
        "priority": "screen"
    }
    res = client.post("/api/recommend", json=payload)
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    top_titles = [i["title"] for i in items]
    assert any("iPad Pro" in t or "Galaxy Tab S10" in t for t in top_titles)
    assert all(0.0 <= item["score"] <= 100.0 for item in items)


