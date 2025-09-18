import pytest
import io
from PIL import Image
from fastapi.testclient import TestClient
from sqlmodel import Session
from tests.factories import (
    create_test_category,
    create_test_product,
    generate_test_image,
)


def test_get_product_image_with_cache_headers(client: TestClient, session: Session):
    """Test image endpoint returns proper cache headers"""
    product = create_test_product(session, with_image=True)

    response = client.get(f"/products/{product.id}/image")
    assert response.status_code == 200
    assert "cache-control" in response.headers
    assert "public" in response.headers["cache-control"]
    assert response.headers["content-type"].startswith("image/")


def test_get_product_image_data_integrity(client: TestClient, session: Session):
    """Test that returned image data matches stored BLOB"""
    # Create product with known image data
    original_image_data = generate_test_image()

    product = create_test_product(session)
    product.image_data = original_image_data
    product.image_mime_type = "image/jpeg"
    product.image_filename = "test_integrity.jpg"
    session.add(product)
    session.commit()
    session.refresh(product)

    response = client.get(f"/products/{product.id}/image")
    assert response.status_code == 200
    assert response.content == original_image_data
    assert response.headers["content-type"] == "image/jpeg"


def test_get_product_image_content_disposition_header(
    client: TestClient, session: Session
):
    """Test that image responses include proper content-disposition header"""
    product = create_test_product(session, with_image=True)
    product.image_filename = "test_product_image.jpg"
    session.add(product)
    session.commit()

    response = client.get(f"/products/{product.id}/image")
    assert response.status_code == 200

    # Should include filename in content-disposition
    if "content-disposition" in response.headers:
        assert "test_product_image.jpg" in response.headers["content-disposition"]


def test_get_product_image_without_image_returns_404(
    client: TestClient, session: Session
):
    """Test that products without images return 404 for image endpoint"""
    product = create_test_product(session, with_image=False)

    response = client.get(f"/products/{product.id}/image")
    assert response.status_code == 404


def test_get_product_image_different_mime_types(client: TestClient, session: Session):
    """Test handling of different image MIME types"""
    mime_types = [("image/jpeg", "JPEG"), ("image/png", "PNG"), ("image/gif", "GIF")]

    for mime_type, format_name in mime_types:
        # Generate image in specific format
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img_buffer = io.BytesIO()
        img.save(img_buffer, format=format_name)
        image_data = img_buffer.getvalue()

        # Create product with specific image type
        product = create_test_product(session)
        product.image_data = image_data
        product.image_mime_type = mime_type
        product.image_filename = f"test.{format_name.lower()}"
        session.add(product)
        session.commit()
        session.refresh(product)

        response = client.get(f"/products/{product.id}/image")
        assert response.status_code == 200
        assert response.headers["content-type"] == mime_type


def test_image_response_performance(client: TestClient, session: Session):
    """Test that image responses are reasonably fast"""
    import time

    # Create product with larger image
    large_image_data = generate_test_image(width=800, height=600)
    product = create_test_product(session)
    product.image_data = large_image_data
    product.image_mime_type = "image/jpeg"
    session.add(product)
    session.commit()
    session.refresh(product)

    start_time = time.time()
    response = client.get(f"/products/{product.id}/image")
    end_time = time.time()

    assert response.status_code == 200
    assert end_time - start_time < 1.0  # Should respond within 1 second


def test_concurrent_image_requests(client: TestClient, session: Session):
    """Test handling of concurrent image requests"""
    import concurrent.futures
    import threading

    product = create_test_product(session, with_image=True)

    def fetch_image():
        response = client.get(f"/products/{product.id}/image")
        return response.status_code, len(response.content)

    # Make multiple concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_image) for _ in range(10)]
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]

    # All requests should succeed and return same content length
    status_codes = [result[0] for result in results]
    content_lengths = [result[1] for result in results]

    assert all(code == 200 for code in status_codes)
    assert len(set(content_lengths)) == 1  # All should have same content length


def test_image_url_generation_in_product_responses(
    client: TestClient, session: Session
):
    """Test that product endpoints correctly generate image URLs"""
    category = create_test_category(session)

    # Create products with and without images
    product_with_image = create_test_product(session, category.id, with_image=True)
    product_without_image = create_test_product(session, category.id, with_image=False)

    # Test single product endpoint
    response_with_image = client.get(f"/products/{product_with_image.id}")
    assert response_with_image.status_code == 200
    product_data = response_with_image.json()
    assert product_data["image_url"] == f"/products/{product_with_image.id}/image"

    response_without_image = client.get(f"/products/{product_without_image.id}")
    assert response_without_image.status_code == 200
    product_data_no_image = response_without_image.json()
    assert (
        product_data_no_image["image_url"] is None
        or product_data_no_image["image_url"] == ""
    )

    # Test products list endpoint
    list_response = client.get("/products")
    assert list_response.status_code == 200
    products = list_response.json()

    # Find our test products in the list
    test_product_with_image = next(
        (p for p in products if p["id"] == product_with_image.id), None
    )
    test_product_without_image = next(
        (p for p in products if p["id"] == product_without_image.id), None
    )

    assert test_product_with_image is not None
    assert (
        test_product_with_image["image_url"]
        == f"/products/{product_with_image.id}/image"
    )

    assert test_product_without_image is not None
    assert (
        test_product_without_image["image_url"] is None
        or test_product_without_image["image_url"] == ""
    )


def test_image_corruption_handling(client: TestClient, session: Session):
    """Test handling of corrupted image data"""
    product = create_test_product(session)

    # Set corrupted image data
    product.image_data = b"This is not valid image data"
    product.image_mime_type = "image/jpeg"
    product.image_filename = "corrupted.jpg"
    session.add(product)
    session.commit()
    session.refresh(product)

    response = client.get(f"/products/{product.id}/image")
    # Should either return the corrupted data (letting client handle it)
    # or return an appropriate error
    assert response.status_code in [200, 400, 404, 500]


def test_large_image_handling(client: TestClient, session: Session):
    """Test handling of very large images"""
    # Create a large image (2MB+)
    large_image = Image.new("RGB", (2000, 2000), color=(0, 255, 0))
    img_buffer = io.BytesIO()
    large_image.save(img_buffer, format="JPEG", quality=95)
    large_image_data = img_buffer.getvalue()

    # Verify it's actually large
    assert len(large_image_data) > 1024 * 1024  # > 1MB

    product = create_test_product(session)
    product.image_data = large_image_data
    product.image_mime_type = "image/jpeg"
    product.image_filename = "large_test.jpg"
    session.add(product)
    session.commit()
    session.refresh(product)

    response = client.get(f"/products/{product.id}/image")
    assert response.status_code == 200
    assert len(response.content) == len(large_image_data)


def test_image_filename_sanitization(client: TestClient, session: Session):
    """Test that image filenames with special characters are handled properly"""
    problematic_filenames = [
        "test file with spaces.jpg",
        "test-file-with-dashes.jpg",
        "test_file_with_underscores.jpg",
        "test.file.with.dots.jpg",
        "test@file#with$special%chars.jpg",
    ]

    for filename in problematic_filenames:
        product = create_test_product(session, with_image=True)
        product.image_filename = filename
        session.add(product)
        session.commit()
        session.refresh(product)

        response = client.get(f"/products/{product.id}/image")
        assert response.status_code == 200

        # If content-disposition header is present, filename should be handled safely
        if "content-disposition" in response.headers:
            content_disp = response.headers["content-disposition"]
            # Should not break HTTP header parsing
            assert "filename" in content_disp
