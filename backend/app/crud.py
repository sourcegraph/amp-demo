import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from typing import List, Optional, Union
from .models import Product, Category
from .schemas import ProductCreate, ProductUpdate, CategoryCreate
import requests
from PIL import Image
import io

from logging_config import get_logger

logger = get_logger(__name__)

def create_category(session: Session, category: CategoryCreate) -> Category:
    db_category = Category.model_validate(category)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

def get_category_by_name(session: Session, name: str) -> Optional[Category]:
    statement = select(Category).where(Category.name == name)
    return session.exec(statement).first()

def get_categories(session: Session) -> List[Category]:
    statement = select(Category)
    return list(session.exec(statement).all())

def get_category(session: Session, category_id: int) -> Optional[Category]:
    return session.get(Category, category_id)

def create_product(session: Session, product: ProductCreate) -> Product:
    db_product = Product.model_validate(product)
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

def get_products(session: Session, category_id: Optional[int] = None) -> List[Product]:
    from sqlmodel import select
    statement = select(Product).join(Category)
    if category_id:
        statement = statement.where(Product.category_id == category_id)
    return list(session.exec(statement).all())

def get_product(session: Session, product_id: int) -> Optional[Product]:
    return session.get(Product, product_id)

def update_product(session: Session, product_id: int, product_update: ProductUpdate) -> Optional[Product]:
    from datetime import datetime, timezone
    
    db_product = session.get(Product, product_id)
    if not db_product:
        return None
    
    update_data = product_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    # Update the timestamp
    db_product.updated_at = datetime.now(timezone.utc)
    
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

def delete_product(session: Session, product_id: int) -> bool:
    db_product = session.get(Product, product_id)
    if not db_product:
        return False
    
    session.delete(db_product)
    session.commit()
    return True

def create_placeholder_image(session: Session, product: Product) -> bool:
    """Create a placeholder image for the product"""
    try:
        from PIL import ImageDraw, ImageFont
        
        # Create a simple placeholder image with beige background (sand.100)
        width, height = 300, 300
        image = Image.new('RGB', (width, height), color=(245, 245, 244))
        draw = ImageDraw.Draw(image)
        
        # Draw a border
        draw.rectangle([10, 10, width-10, height-10], outline=(200, 200, 200), width=2)
        
        # Add text (product title truncated)
        title = product.title[:30] + "..." if len(product.title) > 30 else product.title
        
        # Try to use a font, fallback to default if not available
        try:
            font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont] = ImageFont.truetype("Arial", 16)
        except OSError:
            font = ImageFont.load_default()
        
        # Calculate text position (center it)
        text_bbox = draw.textbbox((0, 0), title, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), title, fill=(100, 100, 100), font=font)
        
        # Add category text below
        category_text = f"Category: {product.category.name if product.category else 'Unknown'}"
        cat_bbox = draw.textbbox((0, 0), category_text, font=font)
        cat_width = cat_bbox[2] - cat_bbox[0]
        cat_x = (width - cat_width) // 2
        draw.text((cat_x, y + 30), category_text, fill=(150, 150, 150), font=font)
        
        # Save image to bytes buffer
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='JPEG', quality=85)
        img_buffer.seek(0)
        
        # Store in database
        product.image_data = img_buffer.getvalue()
        product.image_mime_type = 'image/jpeg'
        product.image_filename = f"placeholder_{product.id}.jpg"
        
        session.add(product)
        session.commit()
        return True
        
    except Exception as e:
        logger.error(
            "placeholder_image_error",
            product_id=product.id,
            error=str(e),
        )
        return False

def download_and_store_image(session: Session, product: Product, image_url: str) -> bool:
    """Download image from URL and store as BLOB in database. Fallback to placeholder if failed."""
    try:
        # Add user agent to avoid bot detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        # Download image
        response = requests.get(image_url, timeout=30, headers=headers)
        response.raise_for_status()
        
        # Open image with PIL to validate and get format
        raw_image: Image.Image = Image.open(io.BytesIO(response.content))
        
        # Save image to bytes buffer as PNG to preserve transparency
        img_buffer = io.BytesIO()
        raw_image.save(img_buffer, format='PNG', optimize=True)
        img_buffer.seek(0)
        
        # Store in database
        product.image_data = img_buffer.getvalue()
        product.image_mime_type = 'image/png'
        product.image_filename = f"product_{product.id}.png"
        
        session.add(product)
        session.commit()
        return True
        
    except Exception as e:
        logger.warning(
            "image_download_failed",
            product_id=product.id,
            image_url=image_url,
            error=str(e),
            fallback="placeholder",
        )
        return create_placeholder_image(session, product)
