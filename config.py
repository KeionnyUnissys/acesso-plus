import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    # Chave usada para assinar a sessão e os tokens CSRF. Em produção, defina no .env.
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-troque-esta-chave")

    # Sem DATABASE_URL, usa SQLite local (não precisa instalar nada).
    # Para PostgreSQL: DATABASE_URL=postgresql+psycopg://usuario:senha@localhost:5432/acesso_plus
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'acesso_plus.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cookies de sessão mais seguros
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"  # 1 quando estiver em HTTPS
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "teste"
