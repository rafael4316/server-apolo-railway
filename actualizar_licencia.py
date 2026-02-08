import os
import requests

BASE_URL = "https://licencia-autoclave.onrender.com"
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

if not ADMIN_TOKEN:
    raise RuntimeError("❌ ADMIN_TOKEN no definido.")

payload = {
    "admin_token": ADMIN_TOKEN,
    "username": "RAFAE_007",
    "new_expiration_date": "2026-06-30"
}

response = requests.post(
    f"{BASE_URL}/update_expiration",
    json=payload,
    timeout=10
)

if response.status_code == 200:
    print("✅ Licencia actualizada correctamente.")
else:
    print(f"❌ Error {response.status_code}: {response.text}")
