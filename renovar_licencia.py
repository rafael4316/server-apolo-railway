import requests

BASE_URL = "https://server-apolo-railway-production.up.railway.app"
ADMIN_TOKEN = "R4f43l_AP0L0_Secr3t_2025!!"  # mismo token de Railway

payload = {
    "admin_token": ADMIN_TOKEN,
    "username": "RAFAE_007",
    "new_expiration_date": "2026-06-30"
}

response = requests.post(
    f"{BASE_URL}/renew_license",
    json=payload,
    timeout=10
)

if response.status_code == 200:
    print("✅ Licencia renovada correctamente.")
    print(response.json())
else:
    print(f"❌ Error {response.status_code}: {response.text}")
