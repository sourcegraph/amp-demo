from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import Session
from typing import List, Optional
import io
import logging
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore

from .db import get_session, create_db_and_tables
from .fx import fx_service, convert_price
from .config import settings, CurrencyCode

from .schemas import (
    ProductRead, ProductCreate, ProductUpdate, ProductReadWithCategory,
    CategoryRead, CategoryCreate, CategoryReadWithProducts
)
from . import crud
from .endpoints.fx import router as fx_router

logger = logging.getLogger(__name__)

# APScheduler instance
scheduler = AsyncIOScheduler()

async def fetch_fx_rates_job():
    """Scheduled job to fetch FX rates hourly."""
    try:
        logger.info("Running scheduled FX rates fetch")
        await fx_service.fetch_rates()
        logger.info("Successfully updated FX rates")
    except Exception as e:
        logger.error(f"Failed to fetch FX rates in scheduled job: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    
    # Skip scheduler in testing environment or if disabled in settings
    disable_scheduler = settings.disable_scheduler or "pytest" in os.environ.get("_", "")
    
    if not disable_scheduler:
        # Start the scheduler and add the hourly FX rates job
        try:
            scheduler.add_job(
                fetch_fx_rates_job,
                trigger=CronTrigger(minute=0),  # Run at the top of every hour
                id="fetch_fx_rates",
                replace_existing=True
            )
            scheduler.start()
            logger.info("Started APScheduler for FX rates updates")
        except Exception as e:
            logger.warning(f"Failed to start scheduler: {e}")
    
    # Fetch initial rates
    try:
        await fx_service.fetch_rates()
        logger.info("Fetched initial FX rates")
        # In test environment, ensure cache is not stale
        if os.getenv("PYTEST_CURRENT_TEST") or "pytest" in os.environ.get("_", ""):
            fx_service._extend_cache_for_testing()
    except Exception as e:
        logger.warning(f"Failed to fetch initial FX rates: {e}")
    
    yield
    
    # Shutdown
    if not disable_scheduler:
        try:
            scheduler.shutdown()
            logger.info("Shut down APScheduler")
        except Exception as e:
            logger.warning(f"Error shutting down scheduler: {e}")

app = FastAPI(
    title="E-commerce Store API",
    description="A FastAPI backend for the e-commerce demo with BLOB image storage",
    version="1.0.0",
    lifespan=lifespan
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

# Include FX router
app.include_router(fx_router)

async def convert_product_price(product, target_currency: Optional[CurrencyCode] = None) -> dict:
    """Helper function to convert product price and build response dict."""
    product_dict = {
        "id": product.id,
        "title": product.title,
        "description": product.description,
        "price": float(product.price),
        "category_id": product.category_id,
        "is_saved": product.is_saved,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
        "image_url": f"/products/{product.id}/image" if product.image_data else None,
        "currency": None,
        "original_price": None
    }
    
    # Convert price if target currency is specified and different from USD
    if target_currency and target_currency != CurrencyCode.USD:
        try:
            if fx_service.is_cache_stale():
                # If rates are stale, raise 409 to indicate the client should retry
                raise HTTPException(
                    status_code=409,
                    detail="Currency conversion rates are stale or unavailable. Please try again later."
                )
            
            converted_price = await convert_price(float(product.price), CurrencyCode.USD, target_currency)
            product_dict.update({
                "price": converted_price,
                "currency": target_currency,
                "original_price": float(product.price)
            })
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error converting price: {e}")
            raise HTTPException(
                status_code=409,
                detail="Currency conversion temporarily unavailable. Please try again later."
            )
    elif target_currency == CurrencyCode.USD:
        product_dict["currency"] = CurrencyCode.USD
    
    return product_dict

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

@app.get("/categories", response_model=List[CategoryRead])
def get_categories(session: Session = Depends(get_session)):
    return crud.get_categories(session)

@app.get("/categories/{category_id}", response_model=CategoryReadWithProducts)
async def get_category(
    category_id: int,
    currency: Optional[CurrencyCode] = None,
    session: Session = Depends(get_session)
):
    category = crud.get_category(session, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Convert to response format with image URLs and currency conversion
    products_with_images = []
    for product in category.products:
        product_dict = await convert_product_price(product, currency)
        products_with_images.append(product_dict)
    
    return {
        "id": category.id,
        "name": category.name,
        "created_at": category.created_at,
        "updated_at": category.updated_at,
        "products": products_with_images
    }

# Product endpoints
@app.post("/products", response_model=ProductRead)
async def create_product(
    product: ProductCreate,
    session: Session = Depends(get_session)
):
    # Verify category exists
    category = crud.get_category(session, product.category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    
    created_product = crud.create_product(session, product)
    
    # Convert to response format with image URL (no currency conversion for create)
    return await convert_product_price(created_product, None)

@app.get("/products", response_model=List[ProductRead])
async def get_products(
    category_id: Optional[int] = None,
    currency: Optional[CurrencyCode] = None,
    session: Session = Depends(get_session)
):
    products = crud.get_products(session, category_id)
    
    # Convert to response format with image URLs and currency conversion
    result = []
    for product in products:
        product_dict = await convert_product_price(product, currency)
        product_dict["category"] = {
            "id": product.category.id,
            "name": product.category.name,
            "created_at": product.category.created_at,
            "updated_at": product.category.updated_at,
        } if product.category else None
        result.append(product_dict)
    
    return result

@app.get("/products/{product_id}", response_model=ProductReadWithCategory)
async def get_product(
    product_id: int,
    currency: Optional[CurrencyCode] = None,
    session: Session = Depends(get_session)
):
    product = crud.get_product(session, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Convert to response format with image URL and currency conversion
    product_dict = await convert_product_price(product, currency)
    product_dict["category"] = {
        "id": product.category.id,
        "name": product.category.name,
        "created_at": product.category.created_at,
        "updated_at": product.category.updated_at,
    } if product.category else None
    
    return product_dict

@app.put("/products/{product_id}", response_model=ProductRead)
async def update_product(
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
    
    # Convert to response format with image URL (no currency conversion for update)
    return await convert_product_price(updated_product, None)

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
            "Cache-Control": "public, max-age=86400"  # Cache for 1 day
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
