import os
import shutil
from typing import Optional, List

from fastapi import FastAPI, UploadFile, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, insert, text
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

from db import engine, get_db
from models import metadata, users, posts

# --- konfiguracja
API_TITLE = "Tourismo API"
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title=API_TITLE)

# CORS (pozwól na dostęp z aplikacji mobilnej / emulatora)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # w produkcji zawęź
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount statyczny do zdjęć
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Inicjalizacja tabel
with engine.begin() as conn:
    # Stwórz DB jeśli brak (przy połączeniu do istniejącej bazy można pominąć)
    conn.execute(text("SET sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));"))
metadata.create_all(bind=engine)

# --- Schematy odpowiedzi (proste słowniki)

@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/register")
def register(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # sprawdź czy istnieje
    exists: Optional[tuple] = db.execute(select(users.c.id).where(users.c.email == email)).fetchone()
    if exists:
        raise HTTPException(status_code=400, detail="Użytkownik o takim e-mailu już istnieje.")
    db.execute(insert(users).values(email=email, password=generate_password_hash(password)))
    db.commit()
    return {"ok": True}

@app.post("/api/login")
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    row = db.execute(select(users).where(users.c.email == email)).first()
    if not row:
        raise HTTPException(status_code=401, detail="Błędny e-mail lub hasło.")
    # row to Row(users..., ) -> dostęp po kolumnach
    if not check_password_hash(row.password, password):
        raise HTTPException(status_code=401, detail="Błędny e-mail lub hasło.")
    return {"ok": True, "user_id": int(row.id), "email": row.email}

@app.post("/api/upload")
def upload_post(
    user_id: int = Form(...),
    lat: Optional[float] = Form(None),
    lon: Optional[float] = Form(None),
    file: UploadFile = Form(...),
    db: Session = Depends(get_db),
):
    # Walidacja: czy user istnieje
    if not db.execute(select(users.c.id).where(users.c.id == user_id)).first():
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje.")

    # Zapis pliku
    filename = file.filename or "photo.jpg"
    safe_name = f"{user_id}_{filename}".replace("..", ".")
    dest_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(dest_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    # Zapis wpisu
    db.execute(
        insert(posts).values(
            user_id=user_id,
            photo_path=safe_name,
            lat=lat,
            lon=lon,
        )
    )
    db.commit()
    return {"ok": True, "photo_url": f"/uploads/{safe_name}"}

@app.get("/api/feed")
def get_feed(db: Session = Depends(get_db)) -> List[dict]:
    # proste JOIN + sort DESC
    result: Result = db.execute(
        text("""
            SELECT p.id, p.photo_path, p.lat, p.lon, p.created_at, u.email
            FROM posts p
            JOIN users u ON u.id = p.user_id
            ORDER BY p.created_at DESC
            LIMIT 100
        """)
    )
    items = []
    for row in result.mappings():
        items.append({
            "id": int(row["id"]),
            "user": row["email"],
            "photo": row["photo_path"],
            "lat": row["lat"],
            "lon": row["lon"],
            "created_at": str(row["created_at"]),
        })
    return items
