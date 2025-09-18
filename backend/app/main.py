from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session
from typing import List, Optional
import io

from .db import get_session, create_db_and_tables
from .models import Product, Category
from .schemas import (
    ProductRead,
    ProductCreate,
    ProductUpdate,
    ProductReadWithCategory,
    CategoryRead,
    CategoryCreate,
    CategoryReadWithProducts,
)
from . import crud


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
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "E-commerce API is running"}


# Category endpoints
@app.post("/categories", response_model=CategoryRead)
def create_category(category: CategoryCreate, session: Session = Depends(get_session)):
    # Check if category already exists
    existing_category = crud.get_category_by_name(session, category.name)
    if existing_category:
        raise HTTPException(
            status_code=400,
            detail=f"Category with name '{category.name}' already exists",
        )

    return crud.create_category(session, category)


@app.get("/categories", response_model=List[CategoryRead])
def get_categories(session: Session = Depends(get_session)):
    return crud.get_categories(session)


@app.get("/categories/{category_id}", response_model=CategoryReadWithProducts)
def get_category(category_id: int, session: Session = Depends(get_session)):
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
            "image_url": f"/products/{product.id}/image"
            if product.image_data
            else None,
        }
        products_with_images.append(product_dict)

    return {
        "id": category.id,
        "name": category.name,
        "created_at": category.created_at,
        "updated_at": category.updated_at,
        "products": products_with_images,
    }


# Product endpoints
@app.post("/products", response_model=ProductRead)
def create_product(product: ProductCreate, session: Session = Depends(get_session)):
    # Verify category exists
    category = crud.get_category(session, product.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")

    return crud.create_product(session, product)


@app.get("/products", response_model=List[ProductRead])
def get_products(
    category_id: Optional[int] = None, session: Session = Depends(get_session)
):
    products = crud.get_products(session, category_id)

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
            "image_url": f"/products/{product.id}/image"
            if product.image_data
            else None,
            "category": {
                "id": product.category.id,
                "name": product.category.name,
                "created_at": product.category.created_at,
                "updated_at": product.category.updated_at,
            }
            if product.category
            else None,
        }
        result.append(product_dict)

    return result


@app.get("/products/{product_id}", response_model=ProductReadWithCategory)
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = crud.get_product(session, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

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
        }
        if product.category
        else None,
    }

    return product_dict


@app.put("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    session: Session = Depends(get_session),
):
    # If category_id is being updated, verify it exists
    if product_update.category_id:
        category = crud.get_category(session, product_update.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")

    updated_product = crud.update_product(session, product_id, product_update)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Add image URL
    if updated_product.image_data:
        updated_product.image_url = f"/products/{product_id}/image"

    return updated_product


@app.delete("/products/{product_id}")
def delete_product(product_id: int, session: Session = Depends(get_session)):
    if not crud.delete_product(session, product_id):
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Product deleted successfully"}


@app.get("/products/{product_id}/image")
def get_product_image(product_id: int, session: Session = Depends(get_session)):
    product = crud.get_product(session, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product.image_data:
        raise HTTPException(status_code=404, detail="No image found for this product")

    # Return image as streaming response
    image_stream = io.BytesIO(product.image_data)

    return StreamingResponse(
        io.BytesIO(product.image_data),
        media_type=product.image_mime_type or "image/jpeg",
        headers={
            "Content-Disposition": f'inline; filename="{product.image_filename or f"product_{product_id}.jpg"}"',
            "Cache-Control": "public, max-age=86400",  # Cache for 1 day
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
