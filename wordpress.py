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
    headers = get_auth_header()
    headers["Content-Disposition"] = f"attachment; filename={filename}"
    headers["Content-Type"] = "image/jpeg"
    headers["User-Agent"] = "Mozilla/5.0"
    response = requests.post(url, headers=headers, data=image_bytes)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    response.raise_for_status()
    return response.json()["id"]
def create_product(research_output, image_id):
    url = f"{WP_URL}/wp-json/wc/v3/products"
    headers = get_auth_header()
    headers["Content-Type"] = "application/json"
    payload = {
        "name": research_output.get("title", ""),
        "description": f"{research_output.get('description', '')}\n\nAuthor: {research_output.get('author_name', '')}\nPublisher: {research_output.get('publisher_name', '')}\nLanguage: {research_output.get('language', '')}\nCover Type: {research_output.get('cover_type', '')}\nAge Group: {research_output.get('age_group', '')}\nWeight: {research_output.get('weight', '')}",
        "images": [{"id": image_id}],
        "status": "publish"
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

    images = [{"id": id} for id in image_ids]

    payload = {
        "name": research_output.get("title", ""),
        "description": f"{research_output.get('description', '')}\n\nAuthor: {research_output.get('author_name', '')}\nPublisher: {research_output.get('publisher_name', '')}\nLanguage: {research_output.get('language', '')}\nCover Type: {research_output.get('cover_type', '')}\nAge Group: {research_output.get('age_group', '')}\nWeight: {research_output.get('weight', '')}",
        "images": images,
        "status": "publish"
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["id"]
