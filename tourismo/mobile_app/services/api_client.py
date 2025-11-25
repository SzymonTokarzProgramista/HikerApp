import os
import requests

# Ustaw IP backendu:
# - Emulator Androida -> host: http://10.0.2.2:8000
# - Telefon w sieci LAN -> np. http://192.168.0.12:8000
API_BASE = os.getenv("TOURISMO_API", "http://127.0.0.1:8000")
API = f"{API_BASE}/api"
UPLOADS = f"{API_BASE}/uploads"

class APIClient:
    def register(self, email, password):
        r = requests.post(f"{API}/register", data={"email": email, "password": password}, timeout=10)
        r.raise_for_status()
        return r.json()

    def login(self, email, password):
        r = requests.post(f"{API}/login", data={"email": email, "password": password}, timeout=10)
        r.raise_for_status()
        return r.json()

    def upload_post(self, user_id, filepath, lat=None, lon=None):
        with open(filepath, "rb") as f:
            files = {"file": (os.path.basename(filepath), f, "image/jpeg")}
            data = {"user_id": str(user_id)}
            if lat is not None: data["lat"] = str(lat)
            if lon is not None: data["lon"] = str(lon)
            r = requests.post(f"{API}/upload", data=data, files=files, timeout=30)
            r.raise_for_status()
            return r.json()

    def get_feed(self):
        r = requests.get(f"{API}/feed", timeout=10)
        r.raise_for_status()
        return r.json()

    def uploads_url(self, path: str) -> str:
        return f"{UPLOADS}/{path.lstrip('/')}"
