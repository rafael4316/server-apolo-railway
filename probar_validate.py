import requests

url = "https://server-apolo-railway-production.up.railway.app/validate"

payload = {
    "username": "Apolo2026_user003",
    "license_key": "855-657-BIO",
    "machine_id": "AQUI_EL_MACHINE_ID_REAL"
}

response = requests.post(url, json=payload)

print("Status:", response.status_code)
print("Respuesta:", response.text)
