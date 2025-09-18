#!/usr/bin/env python3
"""
Database seeding script to import products from the frontend's products.json file
"""

import json
import os
import sys
from pathlib import Path
from sqlmodel import Session

from .db import engine, create_db_and_tables
from .models import Product, Category
from .crud import get_category_by_name, create_category, download_and_store_image
from .schemas import CategoryCreate


def load_products_json():
    """Load products from the JSON file"""
    # Try multiple possible paths for the products.json file
    possible_paths = [
        Path(__file__).parent.parent / "products.json",  # Backend directory
        Path(__file__).parent.parent.parent
        / "src"
        / "context"
        / "products.json",  # Frontend location
    ]

    for products_path in possible_paths:
        if products_path.exists():
            print(f"📄 Loading products from: {products_path}")
            with open(products_path, "r") as f:
                return json.load(f)

    print(f"❌ Products file not found in any of these locations:")
    for path in possible_paths:
        print(f"   - {path}")
    sys.exit(1)


def seed_categories(session: Session, products: list) -> dict:
    """Create categories from product data and return a mapping"""
    # Extract unique categories
    categories = set(product["category"] for product in products)
    category_map = {}

    for category_name in categories:
        # Check if category already exists
        existing_category = get_category_by_name(session, category_name)
        if existing_category:
            category_map[category_name] = existing_category.id
            print(
                f"✅ Category '{category_name}' already exists (ID: {existing_category.id})"
            )
        else:
            # Create new category
            new_category = create_category(session, CategoryCreate(name=category_name))
            category_map[category_name] = new_category.id
            print(f"✅ Created category '{category_name}' (ID: {new_category.id})")

    return category_map


def seed_products(session: Session, products: list, category_map: dict):
    """Create products with image download and storage"""
    print(f"\n📦 Seeding {len(products)} products...")

    for product_data in products:
        # Check if product already exists
        existing_product = session.get(Product, product_data["id"])
        if existing_product:
            print(
                f"⏭️  Product '{product_data['title']}' already exists (ID: {product_data['id']})"
            )
            continue

        # Create new product
        new_product = Product(
            id=product_data["id"],
            title=product_data["title"],
            description=product_data["description"],
            price=float(product_data["price"]),
            category_id=category_map[product_data["category"]],
            is_saved=False,
        )

        session.add(new_product)
        session.commit()
        session.refresh(new_product)

        print(
            f"✅ Created product '{product_data['title']}' (ID: {product_data['id']})"
        )

        # Download and store image
        image_url = product_data.get("image")
        if image_url:
            print(f"🖼️  Downloading image from: {image_url}")
            if download_and_store_image(session, new_product, image_url):
                print(f"✅ Successfully stored image for product {product_data['id']}")
            else:
                print(
                    f"❌ Failed to download/store image for product {product_data['id']}"
                )
        else:
            print(f"⚠️  No image URL found for product {product_data['id']}")


def seed_database(custom_engine=None):
    """Main seeding function"""
    db_engine = custom_engine or engine

    print("🌱 Starting database seeding...")

    # Create tables if they don't exist
    create_db_and_tables()

    # Load products data
    print("📄 Loading products.json...")
    products = load_products_json()

    with Session(db_engine) as session:
        # Seed categories
        print(f"\n📂 Creating categories...")
        category_map = seed_categories(session, products)

        # Seed products
        seed_products(session, products, category_map)

    print(f"\n🎉 Database seeding completed!")
    print(f"   - Categories: {len(category_map)}")
    print(f"   - Products: {len(products)}")
    print("   - All product images downloaded and stored as BLOBs")


if __name__ == "__main__":
    seed_database()
