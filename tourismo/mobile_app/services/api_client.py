# services/api_client.py

BASE_URL = "http://127.0.0.1:8000/api" 

import requests

class APIClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")

    def register(self, email: str, password: str):
        resp = requests.post(
            f"{self.base_url}/register",
            data={"email": email, "password": password},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()

    def login(self, email: str, password: str):
        resp = requests.post(
            f"{self.base_url}/login",
            data={"email": email, "password": password},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json()

    def get_feed(self):
        resp = requests.get(f"{self.base_url}/feed", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def upload_photo(self, user_id: int, filepath: str, lat=None, lon=None):
        files = {"file": open(filepath, "rb")}
        data = {"user_id": user_id}
        if lat is not None and lon is not None:
            data["lat"] = lat
            data["lon"] = lon

        resp = requests.post(
            f"{self.base_url}/upload",
            data=data,
            files=files,
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()
