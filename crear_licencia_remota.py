import requests

# 🔗 URL CORRECTA de tu servidor en Render
url = "https://server-apolo-railway-production.up.railway.app/create_license"


# 🔐 USA EXACTAMENTE el mismo ADMIN_TOKEN que pusiste en Render
payload = {
    "admin_token": "R4f43l_AP0L0_Secr3t_2025!!",
    "username": "prueba1",
    "password": "prueba2",
    "license_key": "855-555-BIO",
    "expiration_date": "2026-12-30"
}

try:
    response = requests.post(url, json=payload, timeout=10)

    print("Status:", response.status_code)
    print("Respuesta:", response.text)

    if response.status_code == 200:
        print("✅ Licencia creada correctamente.")
    else:
        print("❌ No se pudo crear la licencia.")

except requests.exceptions.RequestException as e:
    print("❌ Error de conexión:", e)
