from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List, Optional, cast, Any
from sqlalchemy.sql.elements import ColumnElement
import io
import os

from .db import get_session, create_db_and_tables

from .schemas import (
    ProductRead, ProductCreate, ProductUpdate,
    ProductReadWithDeliveryOptions, DeliverySummary,
    CategoryRead, CategoryCreate, CategoryReadWithProducts,
    DeliveryOptionRead
)
from . import crud
from .models import Product, DeliveryOption, Category, ProductDeliveryLink

def calculate_delivery_summary(delivery_options: List[DeliveryOption]) -> Optional[DeliverySummary]:
    """Calculate delivery summary from a list of delivery options"""
    active_options = [opt for opt in delivery_options if opt.is_active]
    if not active_options:
        return None
    
    cheapest = min(active_options, key=lambda o: o.price)
    fastest_min = min(opt.estimated_days_min for opt in active_options)
    fastest_max = min(opt.estimated_days_max for opt in active_options if opt.estimated_days_min == fastest_min)
    
    return DeliverySummary(
        has_free=any(opt.price == 0 for opt in active_options),
        cheapest_price=cheapest.price,
        fastest_days_min=fastest_min,
        fastest_days_max=fastest_max,
        options_count=len(active_options)
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (if needed)

app = FastAPI(
    title="E-commerce Store API",
    description="A FastAPI backend for the e-commerce demo with BLOB image storage",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
origins = os.getenv(
    "CORS_ALLOW_ORIGINS", 
    "http://localhost:3001,http://127.0.0.1:3001"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "E-commerce API is running"}

# Category endpoints
@app.post("/categories", response_model=CategoryRead)
def create_category(
    category: CategoryCreate,
    session: Session = Depends(get_session)
):
    # Check if category already exists
    existing_category = crud.get_category_by_name(session, category.name)
    if existing_category:
        raise HTTPException(
            status_code=400,
            detail=f"Category with name '{category.name}' already exists"
        )
    
    return crud.create_category(session, category)

# New endpoint for dropdown filtering - only categories with products
@app.get("/api/categories", response_model=List[CategoryRead])
def get_categories_for_filter(session: Session = Depends(get_session)):
    """Get categories that have at least one product for dropdown filtering"""
    stmt = (
        select(Category)
        .join(Product)
        .distinct()
        .order_by(Category.name)
    )
    return session.exec(stmt).all()

@app.get("/categories", response_model=List[CategoryRead])
def get_categories(session: Session = Depends(get_session)):
    return crud.get_categories(session)

@app.get("/categories/{category_id}", response_model=CategoryReadWithProducts)
def get_category(
    category_id: int,
    session: Session = Depends(get_session)
):
    category = crud.get_category(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Convert to response format with image URLs
    products_with_images = []
    for product in category.products:
        product_dict = {
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "category_id": product.category_id,
            "is_saved": product.is_saved,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "image_url": f"/products/{product.id}/image" if product.image_data else None,
        }
        products_with_images.append(product_dict)
    
    return {
        "id": category.id,
        "name": category.name,
        "created_at": category.created_at,
        "updated_at": category.updated_at,
        "products": products_with_images
    }

# New endpoint for dropdown filtering - active delivery options
@app.get("/api/delivery-options", response_model=List[DeliveryOptionRead])
def get_delivery_options_for_filter(session: Session = Depends(get_session)):
    """Get active delivery options for dropdown filtering"""
    stmt = (
        select(DeliveryOption)
        .where(DeliveryOption.is_active)
        .order_by(cast(ColumnElement[int], DeliveryOption.estimated_days_min).asc(), cast(ColumnElement[float], DeliveryOption.price).asc())
    )
    return session.exec(stmt).all()

# Product endpoints
@app.post("/products", response_model=ProductRead)
def create_product(
    product: ProductCreate,
    session: Session = Depends(get_session)
):
    # Verify category exists
    category = crud.get_category(session, product.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    
    created_product = crud.create_product(session, product)
    
    # Convert to response format with image URL
    product_dict = {
        "id": created_product.id,
        "title": created_product.title,
        "description": created_product.description,
        "price": created_product.price,
        "category_id": created_product.category_id,
        "is_saved": created_product.is_saved,
        "created_at": created_product.created_at,
        "updated_at": created_product.updated_at,
        "image_url": f"/products/{created_product.id}/image" if created_product.image_data else None,
    }
    
    return product_dict

# Enhanced API endpoint for filtering and sorting
@app.get("/api/products", response_model=List[ProductRead])
def get_products_api(
    categoryId: Optional[int] = Query(None),
    deliveryOptionId: Optional[int] = Query(None),
    sort: str = Query("created_desc"),
    include_delivery_summary: bool = Query(True),
    session: Session = Depends(get_session)
):
    """Get products with filtering and sorting for the frontend dropdown functionality"""
    stmt = select(Product).join(Category)
    
    # Apply category filter
    if categoryId:
        stmt = stmt.where(Product.category_id == categoryId)
    
    # Apply delivery option filter
    if deliveryOptionId:
        stmt = stmt.join(ProductDeliveryLink).where(ProductDeliveryLink.delivery_option_id == deliveryOptionId)
    
    # Always load delivery options for sorting and summary
    stmt = stmt.options(selectinload(cast(Any, Product.delivery_options)))
    stmt = stmt.options(selectinload(cast(Any, Product.category)))
    
    if sort == "delivery_fastest":
        products = session.exec(stmt).unique().all()
        products = sorted(
            products,
            key=lambda p: (
                min((opt.estimated_days_min for opt in p.delivery_options if opt.is_active), default=999),
                p.price
            )
        )
    elif sort == "price_asc":
        stmt = stmt.order_by(cast(ColumnElement[float], Product.price).asc())
        products = session.exec(stmt).unique().all()
    elif sort == "price_desc":
        stmt = stmt.order_by(cast(ColumnElement[float], Product.price).desc())
        products = session.exec(stmt).unique().all()
    else:  # created_desc (default)
        stmt = stmt.order_by(cast(ColumnElement, Product.created_at).desc())
        products = session.exec(stmt).unique().all()
    
    # Convert to response format
    result = []
    for product in products:
        product_dict = {
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "category_id": product.category_id,
            "is_saved": product.is_saved,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "image_url": f"/products/{product.id}/image" if product.image_data else None,
            "category": {
                "id": product.category.id,
                "name": product.category.name,
                "created_at": product.category.created_at,
                "updated_at": product.category.updated_at,
            } if product.category else None,
            "delivery_summary": None
        }
        
        if include_delivery_summary and hasattr(product, 'delivery_options'):
            summary = calculate_delivery_summary(product.delivery_options)
            if summary:
                product_dict["delivery_summary"] = summary.model_dump()
        
        result.append(product_dict)
    
    return result

@app.get("/products", response_model=List[ProductRead])
def get_products(
    category_id: Optional[int] = None,
    include_delivery_summary: bool = Query(False),
    session: Session = Depends(get_session)
):
    stmt = select(Product).join(Category)
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    
    if include_delivery_summary:
        stmt = stmt.options(selectinload(cast(Any, Product.delivery_options)))
    
    stmt = stmt.options(selectinload(cast(Any, Product.category)))
    products = session.exec(stmt).all()
    
    # Convert to response format with image URLs
    result = []
    for product in products:
        product_dict = {
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "category_id": product.category_id,
            "is_saved": product.is_saved,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
            "image_url": f"/products/{product.id}/image" if product.image_data else None,
            "category": {
                "id": product.category.id,
                "name": product.category.name,
                "created_at": product.category.created_at,
                "updated_at": product.category.updated_at,
            } if product.category else None,
            "delivery_summary": None
        }
        
        if include_delivery_summary and hasattr(product, 'delivery_options'):
            summary = calculate_delivery_summary(product.delivery_options)
            if summary:
                product_dict["delivery_summary"] = summary.model_dump()
        
        result.append(product_dict)
    
    return result

@app.get("/products/{product_id}", response_model=ProductReadWithDeliveryOptions)
def get_product(
    product_id: int,
    session: Session = Depends(get_session)
):
    stmt = (
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(cast(Any, Product.delivery_options)))
        .options(selectinload(cast(Any, Product.category)))
    )
    product = session.exec(stmt).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Filter active options and sort them
    active_options = [opt for opt in product.delivery_options if opt.is_active]
    speed_order = {"standard": 0, "express": 1, "next_day": 2, "same_day": 3}
    active_options_sorted = sorted(active_options, key=lambda o: (o.price, speed_order.get(o.speed.value, 999)))
    
    # Convert to response format with image URL
    product_dict = {
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "price": product.price,
        "category_id": product.category_id,
        "is_saved": product.is_saved,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "image_url": f"/products/{product.id}/image" if product.image_data else None,
        "category": {
            "id": product.category.id,
            "name": product.category.name,
            "created_at": product.category.created_at,
            "updated_at": product.category.updated_at,
        } if product.category else None,
        "delivery_options": [
            {
                "id": opt.id,
                "name": opt.name,
                "description": opt.description,
                "speed": opt.speed,
                "price": opt.price,
                "min_order_amount": opt.min_order_amount,
                "estimated_days_min": opt.estimated_days_min,
                "estimated_days_max": opt.estimated_days_max,
                "is_active": opt.is_active,
                "created_at": opt.created_at,
                "updated_at": opt.updated_at,
            }
            for opt in active_options_sorted
        ]
    }
    
    return product_dict

@app.put("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    session: Session = Depends(get_session)
):
    # If category_id is being updated, verify it exists
    if product_update.category_id:
        category = crud.get_category(session, product_update.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    updated_product = crud.update_product(session, product_id, product_update)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Convert to response format with image URL
    product_dict = {
        "id": updated_product.id,
        "title": updated_product.title,
        "description": updated_product.description,
        "price": updated_product.price,
        "category_id": updated_product.category_id,
        "is_saved": updated_product.is_saved,
        "created_at": updated_product.created_at,
        "updated_at": updated_product.updated_at,
        "image_url": f"/products/{product_id}/image" if updated_product.image_data else None,
    }
    
    return product_dict

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    session: Session = Depends(get_session)
):
    if not crud.delete_product(session, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}

@app.get("/products/{product_id}/image")
def get_product_image(
    product_id: int,
    session: Session = Depends(get_session)
):
    product = crud.get_product(session, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product.image_data:
        raise HTTPException(status_code=404, detail="No image found for this product")
    
    # Return image as streaming response
    return StreamingResponse(
        io.BytesIO(product.image_data),
        media_type=product.image_mime_type or "image/jpeg",
        headers={
            "Content-Disposition": f'inline; filename="{product.image_filename or f"product_{product_id}.jpg"}"',
            "Cache-Control": "public, max-age=86400",
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
