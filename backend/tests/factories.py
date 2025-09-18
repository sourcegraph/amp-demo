from typing import Optional
import io
from PIL import Image
from sqlmodel import Session
from app.models import Category, Product
from app.schemas import CategoryCreate, ProductCreate


def create_test_category(session: Session, name: Optional[str] = None) -> Category:
    """Create a test category with optional name override"""
    if name is None:
        # Get count of existing categories to make unique names
        from sqlmodel import select

        existing_count = len(session.exec(select(Category)).all())
        name = f"Test Category {existing_count + 1}"

    category_data = CategoryCreate(name=name)
    category = Category.model_validate(category_data)
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def create_test_product(
    session: Session,
    category_id: Optional[int] = None,
    title: Optional[str] = None,
    price: Optional[float] = None,
    with_image: bool = False,
) -> Product:
    """Create a test product with configurable options"""
    if category_id is None:
        category = create_test_category(session)
        category_id = category.id

    if title is None:
        # Get count of existing products to make unique titles
        from sqlmodel import select

        existing_count = len(session.exec(select(Product)).all())
        title = f"Test Product {existing_count + 1}"

    if price is None:
        price = 29.99

    # Create Product directly with all required fields
    product = Product(
        title=title,
        description=f"Description for {title}",
        price=price,
        category_id=category_id,
        is_saved=False,
    )

    if with_image:
        product.image_data = generate_test_image()
        product.image_mime_type = "image/jpeg"
        product.image_filename = f"test_{title.replace(' ', '_').lower()}.jpg"

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def generate_test_image(width: int = 300, height: int = 300) -> bytes:
    """Generate a small test image as bytes"""
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    img_buffer = io.BytesIO()
    img.save(img_buffer, format="JPEG", quality=85)
    return img_buffer.getvalue()
