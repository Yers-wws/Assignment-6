"""Database seed script for Voltix TechStore.

Populates categories, promo codes, products, and initial reviews.
Idempotent: safe to run multiple times without creating duplicates.
Note: Technical characteristics (ram_gb, weight_kg, battery_mah, etc.)
are realistic DEMO DATA created for the product advisor recommendation engine.
"""

import os
import sys
import json
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import engine as default_engine, SessionLocal as default_session_factory, Base
from models.orm import Category, Product, ProductReview, PromoCode


def seed_database(target_engine=None, session_factory=None):
    """Seeds the database idempotently, supporting engine/session override for tests."""
    eng = target_engine or default_engine
    sf = session_factory or default_session_factory

    # Ensure tables exist
    Base.metadata.create_all(bind=eng)

    session = sf()

    try:
        # 1. Categories
        categories_data = [
            {"slug": "smartphones", "name": "Smartphones"},
            {"slug": "laptops", "name": "Laptops"},
            {"slug": "tablets", "name": "Tablets"},
            {"slug": "mobile-accessories", "name": "Accessories"},
        ]

        cat_map = {}
        for c_data in categories_data:
            cat = session.query(Category).filter_by(slug=c_data["slug"]).first()
            if not cat:
                cat = Category(slug=c_data["slug"], name=c_data["name"])
                session.add(cat)
                session.flush()
            cat_map[c_data["slug"]] = cat.id

        # 2. Promo Codes
        promos_data = [
            {"code": "TECH10", "discount_percent": 0.10, "is_active": True},
            {"code": "VOLTIX20", "discount_percent": 0.20, "is_active": True},
            {"code": "WELCOME5", "discount_percent": 0.05, "is_active": True},
        ]

        for p_data in promos_data:
            promo = session.query(PromoCode).filter_by(code=p_data["code"]).first()
            if not promo:
                promo = PromoCode(**p_data)
                session.add(promo)

        # 3. Products
        products_data = [
            # 10 SMARTPHONES
            {
                "title": "iPhone 15 Pro",
                "brand": "Apple",
                "category": "smartphones",
                "price": 999.00,
                "discount_percentage": 5.0,
                "stock": 15,
                "description": "Aerospace-grade titanium design with A17 Pro chip and customizable Action button.",
                "thumbnail": "assets/products/iphone-15-pro.webp",
                "images": json.dumps(["https://cdn.dummyjson.com/products/images/smartphones/iPhone%2013%20Pro/1.png"]),
                "ram_gb": 8,
                "storage_gb": 256,
                "weight_kg": 0.187,
                "battery_mah": 3274,
                "camera_mp": 48,
                "gaming_gpu": False,
                "use_cases": "photo,flagship,daily",
                "reviews": [
                    {"reviewer_name": "Alex Smith", "rating": 5, "comment": "Incredible camera performance and battery life!"}
                ]
            },
            {
                "title": "Samsung Galaxy S24 Ultra",
                "brand": "Samsung",
                "category": "smartphones",
                "price": 1199.00,
                "discount_percentage": 10.0,
                "stock": 12,
                "description": "Galaxy AI features, titanium frame, built-in S Pen, and 200MP camera system.",
                "thumbnail": "assets/products/samsung-s24-ultra.webp",
                "images": json.dumps([]),
                "ram_gb": 12,
                "storage_gb": 512,
                "weight_kg": 0.232,
                "battery_mah": 5000,
                "camera_mp": 200,
                "gaming_gpu": False,
                "use_cases": "photo,productivity,battery,flagship",
                "reviews": [
                    {"reviewer_name": "Elena Rostova", "rating": 5, "comment": "Screen is bright outdoors and zoom camera is unbeatable."}
                ]
            },
            {
                "title": "Google Pixel 8 Pro",
                "brand": "Google",
                "category": "smartphones",
                "price": 899.00,
                "discount_percentage": 8.0,
                "stock": 8,
                "description": "Google Tensor G3, best-in-class computational photography, and Android 14.",
                "thumbnail": "assets/products/pixel-8-pro.webp",
                "images": json.dumps([]),
                "ram_gb": 12,
                "storage_gb": 256,
                "weight_kg": 0.213,
                "battery_mah": 5050,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "photo,ai,daily",
                "reviews": []
            },
            {
                "title": "iPhone 15",
                "brand": "Apple",
                "category": "smartphones",
                "price": 799.00,
                "discount_percentage": 4.0,
                "stock": 20,
                "description": "Dynamic Island, 48MP main camera, and USB-C in a durable color-infused glass design.",
                "thumbnail": "assets/products/iphone-15.webp",
                "images": json.dumps([]),
                "ram_gb": 6,
                "storage_gb": 128,
                "weight_kg": 0.171,
                "battery_mah": 3349,
                "camera_mp": 48,
                "gaming_gpu": False,
                "use_cases": "daily,photo",
                "reviews": []
            },
            {
                "title": "Samsung Galaxy S24",
                "brand": "Samsung",
                "category": "smartphones",
                "price": 799.00,
                "discount_percentage": 5.0,
                "stock": 18,
                "description": "Compact powerhouse with Snapdragon 8 Gen 3 and Dynamic AMOLED 2X display.",
                "thumbnail": "assets/products/samsung-s24.webp",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 256,
                "weight_kg": 0.167,
                "battery_mah": 4000,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "daily,compact",
                "reviews": []
            },
            {
                "title": "Google Pixel 8",
                "brand": "Google",
                "category": "smartphones",
                "price": 699.00,
                "discount_percentage": 6.0,
                "stock": 15,
                "description": "Compact design, Actua display, and powerful Google Tensor G3 photography algorithms.",
                "thumbnail": "assets/products/pixel-8.webp",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 128,
                "weight_kg": 0.187,
                "battery_mah": 4575,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "photo,daily,compact",
                "reviews": []
            },
            {
                "title": "Xiaomi 14 Pro",
                "brand": "Xiaomi",
                "category": "smartphones",
                "price": 849.00,
                "discount_percentage": 7.0,
                "stock": 10,
                "description": "Leica Summilux optical lens, Snapdragon 8 Gen 3, and 120W HyperCharge.",
                "thumbnail": "assets/products/xiaomi-14-pro.png",
                "images": json.dumps([]),
                "ram_gb": 12,
                "storage_gb": 256,
                "weight_kg": 0.223,
                "battery_mah": 4880,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "photo,gaming,flagship",
                "reviews": []
            },
            {
                "title": "OnePlus 12",
                "brand": "OnePlus",
                "category": "smartphones",
                "price": 799.00,
                "discount_percentage": 9.0,
                "stock": 11,
                "description": "5400 mAh battery, 100W SUPERVOOC charging, and 4th Gen Hasselblad Camera.",
                "thumbnail": "assets/products/oneplus-12.png",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 512,
                "weight_kg": 0.220,
                "battery_mah": 5400,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "battery,gaming,flagship",
                "reviews": []
            },
            {
                "title": "ASUS ROG Phone 8 Pro",
                "brand": "ASUS",
                "category": "smartphones",
                "price": 1199.00,
                "discount_percentage": 5.0,
                "stock": 6,
                "description": "Ultimate mobile gaming with 165Hz AMOLED, AirTrigger controls, and Matrix display.",
                "thumbnail": "assets/products/rog-phone-8.webp",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 512,
                "weight_kg": 0.225,
                "battery_mah": 5500,
                "camera_mp": 50,
                "gaming_gpu": True,
                "use_cases": "gaming,battery",
                "reviews": []
            },
            {
                "title": "Samsung Galaxy A55",
                "brand": "Samsung",
                "category": "smartphones",
                "price": 399.00,
                "discount_percentage": 8.0,
                "stock": 25,
                "description": "Premium metal frame, Super AMOLED 120Hz, and reliable 2-day battery life.",
                "thumbnail": "assets/products/samsung-a55.webp",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 128,
                "weight_kg": 0.213,
                "battery_mah": 5000,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "budget,battery,daily",
                "reviews": []
            },

            # 10 LAPTOPS
            {
                "title": 'MacBook Pro 14" M3',
                "brand": "Apple",
                "category": "laptops",
                "price": 1599.00,
                "discount_percentage": 7.0,
                "stock": 10,
                "description": "Blazing-fast M3 chip, Liquid Retina XDR display, up to 22 hours of battery life.",
                "thumbnail": "assets/products/macbook-pro-14.webp",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 512,
                "weight_kg": 1.55,
                "battery_mah": 70000,
                "camera_mp": 2,
                "gaming_gpu": False,
                "use_cases": "dev,office,study",
                "reviews": [
                    {"reviewer_name": "Dmitry K.", "rating": 5, "comment": "Silent under heavy dev workload and phenomenal battery."}
                ]
            },
            {
                "title": 'MacBook Air 13" M2',
                "brand": "Apple",
                "category": "laptops",
                "price": 999.00,
                "discount_percentage": 5.0,
                "stock": 15,
                "description": "Strikingly thin design, 13.6-inch Liquid Retina display, all-day battery life.",
                "thumbnail": "assets/products/macbook-air-13.png",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 256,
                "weight_kg": 1.24,
                "battery_mah": 52600,
                "camera_mp": 2,
                "gaming_gpu": False,
                "use_cases": "office,study,battery",
                "reviews": []
            },
            {
                "title": "Dell XPS 15",
                "brand": "Dell",
                "category": "laptops",
                "price": 1899.00,
                "discount_percentage": 12.0,
                "stock": 5,
                "description": "OLED 3.5K touch display, Intel Core i7, NVIDIA RTX 4060 graphics.",
                "thumbnail": "assets/products/dell-xps-15.webp",
                "images": json.dumps([]),
                "ram_gb": 32,
                "storage_gb": 1024,
                "weight_kg": 1.86,
                "battery_mah": 86000,
                "camera_mp": 2,
                "gaming_gpu": True,
                "use_cases": "dev,gaming,multimedia",
                "reviews": []
            },
            {
                "title": "ASUS ROG Zephyrus G16",
                "brand": "ASUS",
                "category": "laptops",
                "price": 1999.00,
                "discount_percentage": 8.0,
                "stock": 7,
                "description": "Ultra-slim gaming laptop with Intel Core Ultra 9, OLED 240Hz, and RTX 4070.",
                "thumbnail": "assets/products/asus-rog-zephyrus.webp",
                "images": json.dumps([]),
                "ram_gb": 32,
                "storage_gb": 1024,
                "weight_kg": 1.95,
                "battery_mah": 90000,
                "camera_mp": 2,
                "gaming_gpu": True,
                "use_cases": "gaming,dev",
                "reviews": []
            },
            {
                "title": "Lenovo ThinkPad X1 Carbon Gen 11",
                "brand": "Lenovo",
                "category": "laptops",
                "price": 1699.00,
                "discount_percentage": 10.0,
                "stock": 12,
                "description": "Ultralight business flagship laptop with legendary keyboard and MIL-SPEC durability.",
                "thumbnail": "assets/products/lenovo-thinkpad-x1.webp",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 512,
                "weight_kg": 1.12,
                "battery_mah": 57000,
                "camera_mp": 2,
                "gaming_gpu": False,
                "use_cases": "office,study,lightweight",
                "reviews": []
            },
            {
                "title": "HP Spectre x360 14",
                "brand": "HP",
                "category": "laptops",
                "price": 1399.00,
                "discount_percentage": 6.0,
                "stock": 8,
                "description": "2-in-1 convertible laptop with OLED 2.8K display and 9MP AI intelligent camera.",
                "thumbnail": "assets/products/hp-spectre-14.webp",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 1024,
                "weight_kg": 1.44,
                "battery_mah": 66800,
                "camera_mp": 5,
                "gaming_gpu": False,
                "use_cases": "office,study,battery",
                "reviews": []
            },
            {
                "title": "Acer Predator Helios 16",
                "brand": "Acer",
                "category": "laptops",
                "price": 1499.00,
                "discount_percentage": 15.0,
                "stock": 6,
                "description": "High-octane gaming rig with Intel Core i7, 16-inch WQXGA 240Hz, and RTX 4070.",
                "thumbnail": "assets/products/acer-predator-16.webp",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 1024,
                "weight_kg": 2.60,
                "battery_mah": 90000,
                "camera_mp": 2,
                "gaming_gpu": True,
                "use_cases": "gaming",
                "reviews": []
            },
            {
                "title": "ASUS ZenBook 14 OLED",
                "brand": "ASUS",
                "category": "laptops",
                "price": 1099.00,
                "discount_percentage": 5.0,
                "stock": 14,
                "description": "Stunning 3K ASUS Lumina OLED display, lightweight 1.2kg chassis, Intel Core Ultra 7.",
                "thumbnail": "assets/products/asus-zenbook-14.webp",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 512,
                "weight_kg": 1.28,
                "battery_mah": 75000,
                "camera_mp": 2,
                "gaming_gpu": False,
                "use_cases": "office,study,multimedia",
                "reviews": []
            },
            {
                "title": "Lenovo Legion Pro 5",
                "brand": "Lenovo",
                "category": "laptops",
                "price": 1599.00,
                "discount_percentage": 10.0,
                "stock": 9,
                "description": "AI-tuned performance with AMD Ryzen 7 7745HX and NVIDIA GeForce RTX 4070.",
                "thumbnail": "assets/products/lenovo-legion-pro.webp",
                "images": json.dumps([]),
                "ram_gb": 32,
                "storage_gb": 1024,
                "weight_kg": 2.50,
                "battery_mah": 80000,
                "camera_mp": 2,
                "gaming_gpu": True,
                "use_cases": "gaming,dev",
                "reviews": []
            },
            {
                "title": "Dell Inspiron 15",
                "brand": "Dell",
                "category": "laptops",
                "price": 649.00,
                "discount_percentage": 4.0,
                "stock": 20,
                "description": "Essential everyday laptop with Intel Core i5, 120Hz FHD anti-glare display.",
                "thumbnail": "assets/products/dell-inspiron-15.webp",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 512,
                "weight_kg": 1.65,
                "battery_mah": 54000,
                "camera_mp": 2,
                "gaming_gpu": False,
                "use_cases": "study,office",
                "reviews": []
            },

            # TABLETS & ACCESSORIES
            {
                "title": "iPad Air M2 11-inch",
                "brand": "Apple",
                "category": "tablets",
                "price": 599.00,
                "discount_percentage": 5.0,
                "stock": 20,
                "description": "Supercharged by Apple M2 chip with Liquid Retina display and Apple Pencil Pro support.",
                "thumbnail": "assets/products/ipad-air-m2.webp",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 128,
                "weight_kg": 0.462,
                "battery_mah": 28930,
                "camera_mp": 12,
                "gaming_gpu": False,
                "use_cases": "study,multimedia",
                "reviews": []
            },
            {
                "title": "AirPods Pro (2nd Generation)",
                "brand": "Apple",
                "category": "mobile-accessories",
                "price": 249.00,
                "discount_percentage": 10.0,
                "stock": 30,
                "description": "Up to 2x more Active Noise Cancellation with USB-C MagSafe charging case.",
                "thumbnail": "assets/products/airpods-pro.webp",
                "images": json.dumps([]),
                "ram_gb": None,
                "storage_gb": None,
                "weight_kg": 0.056,
                "battery_mah": None,
                "camera_mp": None,
                "gaming_gpu": False,
                "use_cases": "audio,daily",
                "reviews": []
            },
            {
                "title": "Anker Prime 100W GaN Wall Charger",
                "brand": "Anker",
                "category": "mobile-accessories",
                "price": 79.99,
                "discount_percentage": 15.0,
                "stock": 45,
                "description": "Ultra-compact 3-port fast charger with ActiveShield 2.0 temperature monitoring.",
                "thumbnail": "assets/products/anker-charger-100w.webp",
                "images": json.dumps([]),
                "ram_gb": None,
                "storage_gb": None,
                "weight_kg": 0.180,
                "battery_mah": None,
                "camera_mp": None,
                "gaming_gpu": False,
                "use_cases": "charging,travel",
                "reviews": []
            },

            # =========================================================================
            # ACTUAL MODELS (2025-2026 generation)
            # Specs verified via manufacturer data and major tech reviews
            # Note: Demo prices in USD, approximate retail values
            # =========================================================================

            # --- 8 SMARTPHONES (2025-2026) ---
            {
                "title": "iPhone 16 Pro",
                "brand": "Apple",
                "category": "smartphones",
                "price": 999.00,  # demo prices in USD, approximate
                "discount_percentage": 5.0,
                "stock": 15,
                "description": "Grade 5 Titanium design with A18 Pro chip, 48MP Fusion camera system, and Camera Control button.",
                "thumbnail": "assets/products/iphone-16-pro.webp",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 256,
                "weight_kg": 0.199,
                "battery_mah": 3582,
                "camera_mp": 48,
                "gaming_gpu": False,
                "use_cases": "photo,flagship,daily",
                "reviews": [
                    {"reviewer_name": "Marcus Vance", "rating": 5, "comment": "The dedicated camera control button and battery life are noticeable upgrades."}
                ]
            },
            {
                "title": "Samsung Galaxy S25 Ultra",
                "brand": "Samsung",
                "category": "smartphones",
                "price": 1299.00,  # demo prices in USD, approximate
                "discount_percentage": 5.0,
                "stock": 12,
                "description": "Titanium design with Snapdragon 8 Elite, 200MP camera system, built-in S Pen, and Galaxy AI.",
                "thumbnail": "assets/products/samsung-s25-ultra.webp",
                "images": json.dumps([]),
                "ram_gb": 12,
                "storage_gb": 512,
                "weight_kg": 0.218,
                "battery_mah": 5000,
                "camera_mp": 200,
                "gaming_gpu": False,
                "use_cases": "photo,battery,daily,gaming",
                "reviews": [
                    {"reviewer_name": "Dmitry K.", "rating": 5, "comment": "Snapdragon 8 Elite is blisteringly fast, screen anti-reflective coating is top notch."}
                ]
            },
            {
                "title": "Google Pixel 9 Pro",
                "brand": "Google",
                "category": "smartphones",
                "price": 999.00,  # demo prices in USD, approximate
                "discount_percentage": 6.0,
                "stock": 10,
                "description": "Google Tensor G4, Super Res Zoom up to 30x, 16GB RAM, and pro triple camera system with 8K video.",
                "thumbnail": "assets/products/pixel-9-pro.webp",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 256,
                "weight_kg": 0.199,
                "battery_mah": 4700,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "photo,battery,daily",
                "reviews": []
            },
            {
                "title": "OnePlus 13",
                "brand": "OnePlus",
                "category": "smartphones",
                "price": 799.00,  # demo prices in USD, approximate
                "discount_percentage": 8.0,
                "stock": 18,
                "description": "Snapdragon 8 Elite, massive 6000mAh silicon-carbon battery, and Hasselblad 50MP triple camera system.",
                "thumbnail": "assets/products/oneplus-13.png",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 512,
                "weight_kg": 0.213,
                "battery_mah": 6000,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "battery,gaming,daily,photo",
                "reviews": [
                    {"reviewer_name": "Liam Chen", "rating": 5, "comment": "6000mAh battery easily lasts two full days of heavy use!"}
                ]
            },
            {
                "title": "Xiaomi 15",
                "brand": "Xiaomi",
                "category": "smartphones",
                "price": 699.00,  # demo prices in USD, approximate
                "discount_percentage": 7.0,
                "stock": 16,
                "description": "Compact flagship with Snapdragon 8 Elite, Leica Summilux triple 50MP cameras, and 5240mAh battery.",
                "thumbnail": "assets/products/xiaomi-15.png",
                "images": json.dumps([]),
                "ram_gb": 12,
                "storage_gb": 256,
                "weight_kg": 0.191,
                "battery_mah": 5240,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "photo,daily,battery",
                "reviews": []
            },
            {
                "title": "ASUS ROG Phone 9 Pro",
                "brand": "ASUS",
                "category": "smartphones",
                "price": 1199.00,  # demo prices in USD, approximate
                "discount_percentage": 4.0,
                "stock": 8,
                "description": "Ultimate gaming phone with Snapdragon 8 Elite, 185Hz AMOLED, AirTrigger shoulder controls, and 5800mAh battery.",
                "thumbnail": "assets/products/rog-phone-9.webp",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 512,
                "weight_kg": 0.227,
                "battery_mah": 5800,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "gaming,battery",
                "reviews": []
            },
            {
                "title": "Samsung Galaxy S24 FE",
                "brand": "Samsung",
                "category": "smartphones",
                "price": 649.00,  # demo prices in USD, approximate
                "discount_percentage": 10.0,
                "stock": 22,
                "description": "Flagship experience with 6.7-inch Dynamic AMOLED 2X, Galaxy AI, and 50MP pro-grade camera.",
                "thumbnail": "assets/products/samsung-s24-fe.webp",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 128,
                "weight_kg": 0.213,
                "battery_mah": 4700,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "daily,photo,battery",
                "reviews": []
            },
            {
                "title": "iPhone 16",
                "brand": "Apple",
                "category": "smartphones",
                "price": 799.00,  # demo prices in USD, approximate
                "discount_percentage": 5.0,
                "stock": 25,
                "description": "A18 chip, Camera Control, 48MP Fusion camera with 2x Telephoto, and Apple Intelligence.",
                "thumbnail": "assets/products/iphone-16.webp",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 128,
                "weight_kg": 0.170,
                "battery_mah": 3561,
                "camera_mp": 48,
                "gaming_gpu": False,
                "use_cases": "daily,photo",
                "reviews": []
            },

            # --- 8 LAPTOPS (2025-2026) ---
            {
                "title": "MacBook Pro 14 (M4)",
                "brand": "Apple",
                "category": "laptops",
                "price": 1599.00,  # demo prices in USD, approximate
                "discount_percentage": 4.0,
                "stock": 10,
                "description": "Next-gen M4 chip with 10-core CPU, Liquid Retina XDR display, and up to 24 hours of battery life.",
                "thumbnail": "assets/products/macbook-pro-14.webp",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 512,
                "weight_kg": 1.55,
                "battery_mah": 72400,
                "camera_mp": None,
                "gaming_gpu": False,
                "use_cases": "dev,office,study",
                "reviews": [
                    {"reviewer_name": "Sergey P.", "rating": 5, "comment": "Standard 16GB RAM base model with M4 is fantastic for compilation and docker."}
                ]
            },
            {
                "title": "Dell XPS 14 9440",
                "brand": "Dell",
                "category": "laptops",
                "price": 1699.00,  # demo prices in USD, approximate
                "discount_percentage": 6.0,
                "stock": 8,
                "description": "Intel Core Ultra 7 processor, NVIDIA GeForce RTX 4050, CNC machined aluminum, and InfinityEdge display.",
                "thumbnail": "assets/products/dell-xps-14.webp",
                "images": json.dumps([]),
                "ram_gb": 32,
                "storage_gb": 1000,
                "weight_kg": 1.68,
                "battery_mah": 70000,
                "camera_mp": None,
                "gaming_gpu": True,
                "use_cases": "dev,office,study",
                "reviews": []
            },
            {
                "title": "ASUS ROG Zephyrus G16 (2024)",
                "brand": "ASUS",
                "category": "laptops",
                "price": 1999.00,  # demo prices in USD, approximate
                "discount_percentage": 5.0,
                "stock": 6,
                "description": "Ultra-slim gaming powerhouse with Intel Core Ultra 9, RTX 4070, and 2.5K 240Hz OLED display.",
                "thumbnail": "assets/products/asus-rog-zephyrus.webp",
                "images": json.dumps([]),
                "ram_gb": 32,
                "storage_gb": 1000,
                "weight_kg": 1.85,
                "battery_mah": 90000,
                "camera_mp": None,
                "gaming_gpu": True,
                "use_cases": "gaming,dev",
                "reviews": [
                    {"reviewer_name": "Arthur Dent", "rating": 5, "comment": "The OLED panel paired with RTX 4070 in a sub-2kg laptop is extraordinary."}
                ]
            },
            {
                "title": "Lenovo ThinkPad X1 Carbon Gen 12",
                "brand": "Lenovo",
                "category": "laptops",
                "price": 1799.00,  # demo prices in USD, approximate
                "discount_percentage": 8.0,
                "stock": 12,
                "description": "Intel Core Ultra 7 with Intel vPro, ultralight carbon fiber chassis at 1.09 kg, and legendary keyboard.",
                "thumbnail": "assets/products/lenovo-thinkpad-x1.webp",
                "images": json.dumps([]),
                "ram_gb": 32,
                "storage_gb": 1000,
                "weight_kg": 1.09,
                "battery_mah": 57000,
                "camera_mp": None,
                "gaming_gpu": False,
                "use_cases": "office,dev,study",
                "reviews": []
            },
            {
                "title": "Lenovo Legion Pro 7i Gen 9",
                "brand": "Lenovo",
                "category": "laptops",
                "price": 2399.00,  # demo prices in USD, approximate
                "discount_percentage": 7.0,
                "stock": 5,
                "description": "High-performance gaming laptop with Intel Core i9-14900HX, NVIDIA GeForce RTX 4080, and 99.9Wh battery.",
                "thumbnail": "assets/products/lenovo-legion-pro.webp",
                "images": json.dumps([]),
                "ram_gb": 32,
                "storage_gb": 1000,
                "weight_kg": 2.62,
                "battery_mah": 99900,
                "camera_mp": None,
                "gaming_gpu": True,
                "use_cases": "gaming,dev",
                "reviews": []
            },
            {
                "title": "ASUS Zenbook S 14 (UX5406)",
                "brand": "ASUS",
                "category": "laptops",
                "price": 1399.00,  # demo prices in USD, approximate
                "discount_percentage": 5.0,
                "stock": 14,
                "description": "Ceraluminum body, Intel Core Ultra 7 (Series 2), 3K 120Hz OLED, and whisper-quiet cooling.",
                "thumbnail": "assets/products/asus-zenbook-14.webp",
                "images": json.dumps([]),
                "ram_gb": 32,
                "storage_gb": 1000,
                "weight_kg": 1.20,
                "battery_mah": 72000,
                "camera_mp": None,
                "gaming_gpu": False,
                "use_cases": "office,study,dev",
                "reviews": []
            },
            {
                "title": "HP OmniBook X 14",
                "brand": "HP",
                "category": "laptops",
                "price": 1199.00,  # demo prices in USD, approximate
                "discount_percentage": 9.0,
                "stock": 15,
                "description": "Qualcomm Snapdragon X Elite, 26 hours battery life, 2.2K touch display, and next-gen AI processing.",
                "thumbnail": "assets/products/hp-omnibook-14.webp",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 512,
                "weight_kg": 1.34,
                "battery_mah": 59000,
                "camera_mp": None,
                "gaming_gpu": False,
                "use_cases": "office,study,dev",
                "reviews": []
            },
            {
                "title": "Acer Swift 14 AI",
                "brand": "Acer",
                "category": "laptops",
                "price": 999.00,  # demo prices in USD, approximate
                "discount_percentage": 10.0,
                "stock": 18,
                "description": "Intel Core Ultra 7 (Series 2) Copilot+ PC with 2.8K OLED 120Hz display, 65Wh battery, and 1.26 kg chassis.",
                "thumbnail": "assets/products/acer-swift-14.webp",
                "images": json.dumps([]),
                "ram_gb": 16,
                "storage_gb": 1000,
                "weight_kg": 1.26,
                "battery_mah": 65000,
                "camera_mp": None,
                "gaming_gpu": False,
                "use_cases": "study,office,dev",
                "reviews": []
            },

            # --- 4 TABLETS (2025-2026) ---
            {
                "title": "iPad Pro 11 (M4)",
                "brand": "Apple",
                "category": "tablets",
                "price": 999.00,  # demo prices in USD, approximate
                "discount_percentage": 5.0,
                "stock": 14,
                "description": "Ultra Retina XDR Tandem OLED display powered by Apple M4 chip, only 5.3mm thin.",
                "thumbnail": "assets/products/ipad-pro-11.png",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 256,
                "weight_kg": 0.444,
                "battery_mah": 8160,
                "camera_mp": 12,
                "gaming_gpu": False,
                "use_cases": "work,multimedia,study,daily",
                "reviews": [
                    {"reviewer_name": "Elena R.", "rating": 5, "comment": "The tandem OLED screen is unbelievable. So light and responsive."}
                ]
            },
            {
                "title": "Samsung Galaxy Tab S10+",
                "brand": "Samsung",
                "category": "tablets",
                "price": 999.00,  # demo prices in USD, approximate
                "discount_percentage": 8.0,
                "stock": 12,
                "description": "12.4-inch Dynamic AMOLED 2X, MediaTek Dimensity 9300+, S Pen included, IP68 water resistance.",
                "thumbnail": "assets/products/galaxy-tab-s10.webp",
                "images": json.dumps([]),
                "ram_gb": 12,
                "storage_gb": 256,
                "weight_kg": 0.571,
                "battery_mah": 10090,
                "camera_mp": 13,
                "gaming_gpu": False,
                "use_cases": "work,multimedia,daily,study",
                "reviews": []
            },
            {
                "title": "iPad mini (A17 Pro)",
                "brand": "Apple",
                "category": "tablets",
                "price": 499.00,  # demo prices in USD, approximate
                "discount_percentage": 4.0,
                "stock": 20,
                "description": "Ultra-portable 8.3-inch Liquid Retina display with A17 Pro chip and Apple Pencil Pro support.",
                "thumbnail": "assets/products/ipad-mini-a17.webp",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 128,
                "weight_kg": 0.293,
                "battery_mah": 5078,
                "camera_mp": 12,
                "gaming_gpu": False,
                "use_cases": "daily,study,multimedia",
                "reviews": []
            },
            {
                "title": "Xiaomi Pad 6S Pro 12.4",
                "brand": "Xiaomi",
                "category": "tablets",
                "price": 599.00,  # demo prices in USD, approximate
                "discount_percentage": 10.0,
                "stock": 15,
                "description": "12.4-inch 3K 144Hz display, Snapdragon 8 Gen 2, 10000mAh battery with 120W HyperCharge.",
                "thumbnail": "assets/products/xiaomi-pad-6s.webp",
                "images": json.dumps([]),
                "ram_gb": 8,
                "storage_gb": 256,
                "weight_kg": 0.590,
                "battery_mah": 10000,
                "camera_mp": 50,
                "gaming_gpu": False,
                "use_cases": "multimedia,work,study,daily",
                "reviews": []
            },

            # --- 3 ACCESSORIES (2025-2026) ---
            {
                "title": "AirPods 4 with Active Noise Cancellation",
                "brand": "Apple",
                "category": "mobile-accessories",
                "price": 179.00,  # demo prices in USD, approximate
                "discount_percentage": 5.0,
                "stock": 35,
                "description": "Active Noise Cancellation, Transparency mode, Personalized Spatial Audio, and USB-C case with speaker.",
                "thumbnail": "assets/products/airpods-4.webp",
                "images": json.dumps([]),
                "ram_gb": None,
                "storage_gb": None,
                "weight_kg": 0.043,
                "battery_mah": None,
                "camera_mp": None,
                "gaming_gpu": False,
                "use_cases": "audio,daily,travel",
                "reviews": []
            },
            {
                "title": "Samsung Galaxy Buds3 Pro",
                "brand": "Samsung",
                "category": "mobile-accessories",
                "price": 229.00,  # demo prices in USD, approximate
                "discount_percentage": 10.0,
                "stock": 28,
                "description": "Blade design with LED lights, 24-bit Hi-Fi audio, enhanced 2-way speakers, and Adaptive Noise Control.",
                "thumbnail": "assets/products/galaxy-buds-3.webp",
                "images": json.dumps([]),
                "ram_gb": None,
                "storage_gb": None,
                "weight_kg": 0.057,
                "battery_mah": 515,
                "camera_mp": None,
                "gaming_gpu": False,
                "use_cases": "audio,daily,travel",
                "reviews": []
            },
            {
                "title": "Anker MagGo Power Bank 10000mAh",
                "brand": "Anker",
                "category": "mobile-accessories",
                "price": 89.99,  # demo prices in USD, approximate
                "discount_percentage": 12.0,
                "stock": 40,
                "description": "Qi2-certified 15W ultra-fast wireless magnetic charging power bank with smart digital display and kickstand.",
                "thumbnail": "assets/products/anker-maggo-powerbank.webp",
                "images": json.dumps([]),
                "ram_gb": None,
                "storage_gb": None,
                "weight_kg": 0.250,
                "battery_mah": 10000,
                "camera_mp": None,
                "gaming_gpu": False,
                "use_cases": "charging,travel,daily",
                "reviews": []
            },
        ]

        for p_item in products_data:
            item_data = dict(p_item)
            cat_slug = item_data.pop("category")
            reviews_data = item_data.pop("reviews", [])
            cat_id = cat_map[cat_slug]

            prod = session.query(Product).filter_by(title=item_data["title"]).first()
            if not prod:
                prod = Product(
                    category_id=cat_id,
                    **item_data
                )
                session.add(prod)
                session.flush()

                if reviews_data:
                    for r_data in reviews_data:
                        review = ProductReview(
                            product_id=prod.id,
                            reviewer_name=r_data["reviewer_name"],
                            rating=r_data["rating"],
                            comment=r_data["comment"],
                        )
                        session.add(review)
                    session.flush()

                    ratings = [r["rating"] for r in reviews_data]
                    prod.rating = round(sum(ratings) / len(ratings), 1)
                    prod.reviews_count = len(ratings)
            else:
                # Synchronize thumbnails on existing products if updated in seed
                if "thumbnail" in item_data and item_data["thumbnail"]:
                    prod.thumbnail = item_data["thumbnail"]
                if "images" in item_data and item_data["images"]:
                    prod.images = item_data["images"]

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
    print("Database seeded successfully.")
