import os
import requests
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

if not ACCOUNT_ID or not API_TOKEN:
    print("Missing Cloudflare credentials in .env")
    raise SystemExit

url = (
    f"https://api.cloudflare.com/client/v4/accounts/"
    f"{ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
)

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "prompt": "A cute futuristic blue and yellow AI robot named Jenny"
}

print("Connecting to Cloudflare...")
response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=180
)

print("Status Code:", response.status_code)

if response.status_code == 200:
    content_type = response.headers.get("Content-Type", "")

    if "image/" in content_type:
        image_data = response.content
    else:
        data = response.json()
        image_data = __import__("base64").b64decode(
            data["result"]["image"]
        )

    with open("jenny_test_image.jpg", "wb") as file:
        file.write(image_data)

    print("SUCCESS! Jenny generated an image!")
    print("Saved as jenny_test_image.jpg")

else:
    print("API Error:")
    print(response.text)