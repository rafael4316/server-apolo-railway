import requests

BASE_URL = "https://server-apolo-railway-production.up.railway.app"
ADMIN_TOKEN = "R4f43l_AP0L0_Secr3t_2025!!"

payload = {
    "admin_token": ADMIN_TOKEN,
    "username": "prueba1"
}

response = requests.post(
    f"{BASE_URL}/suspend_license",
    json=payload,
    timeout=10
)

if response.status_code == 200:
    print("🚫 Licencia suspendida correctamente.")
    print(response.json())
else:
    print(f"❌ Error {response.status_code}: {response.text}")
