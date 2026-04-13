import requests
import base64
import os
from dotenv import load_dotenv

load_dotenv(override=True)

WP_URL = os.getenv("WP_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")

def get_auth_header():
    credentials = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
    token = base64.b64encode(credentials.encode()).decode("utf-8")
    return {"Authorization": f"Basic {token}"}

def upload_image(image_bytes, filename="book_cover.jpg"):
    url = f"{WP_URL}/wp-json/wp/v2/media"
    
    if filename.lower().endswith(".png"):
        content_type = "image/png"
    elif filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
        content_type = "image/jpeg"
    else:
        content_type = "image/jpeg"
    
    headers = get_auth_header()
    headers["Content-Disposition"] = f"attachment; filename={filename}"
    headers["Content-Type"] = content_type

    response = requests.post(url, headers=headers, data=image_bytes)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    response.raise_for_status()
    return response.json()["id"]

def build_attributes(research_output):
    """Build WooCommerce global attributes using correct IDs and slugs from the site."""
    attributes = []

    # (id, slug, key in research_output)
    mapping = [
        (5,  "pa_age-group",      "age_group"),
        (4,  "pa_cover-type",     "cover_type"),
        (6,  "pa_language",       "language"),
        (7,  "pa_author-name",    "author_name"),
        (8,  "pa_publisher-name", "publisher_name"),
    ]

    for position, (attr_id, slug, key) in enumerate(mapping):
        value = research_output.get(key, "")
        if value:
            attributes.append({
                "id": attr_id,
                "name": slug,
                "options": [value],
                "visible": True,
                "variation": False,
                "position": position
            })

    return attributes

def create_product(research_output, image_id):
    url = f"{WP_URL}/wp-json/wc/v3/products"
    headers = get_auth_header()
    headers["Content-Type"] = "application/json"
    payload = {
        "name": research_output.get("title", ""),
        "description": research_output.get("description", ""),
        "images": [{"id": image_id, "position": 0}],
        "status": "publish",
        "attributes": build_attributes(research_output)
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["id"]

def upload_multiple_images(images):
    image_ids = []
    for image_bytes, filename in images:
        image_id = upload_image(image_bytes, filename)
        image_ids.append(image_id)
    return image_ids

def create_product_with_gallery(research_output, image_ids):
    url = f"{WP_URL}/wp-json/wc/v3/products"
    headers = get_auth_header()
    headers["Content-Type"] = "application/json"

    images = [{"id": img_id, "position": i} for i, img_id in enumerate(image_ids)]

    payload = {
        "name": research_output.get("title", ""),
        "description": research_output.get("description", ""),
        "images": images,
        "status": "publish",
        "attributes": build_attributes(research_output),
        "weight": research_output.get("weight", "")
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["id"]
