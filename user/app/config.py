from dotenv import load_dotenv
import os

load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM","HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "10/minute")
DATABASE_URL = os.getenv("DATABASE_URL")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

for _name in ("SECRET_KEY", "DATABASE_URL"):
    if not globals()[_name]:
        raise RuntimeError(f"{_name} is not defined. Copy example_env.txt to .env and complete it.")
