from sqlalchemy import MetaData, Table, Column, Integer, String, Float, DateTime, ForeignKey, func

metadata = MetaData()

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String(120), unique=True, nullable=False),
    Column("password", String(255), nullable=False),  # hash!
)

posts = Table(
    "posts", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("photo_path", String(255), nullable=False),
    Column("lat", Float, nullable=True),
    Column("lon", Float, nullable=True),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
)
