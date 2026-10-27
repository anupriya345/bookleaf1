import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "720"))
database_url = make_url(os.getenv("DATABASE_URL", "sqlite:///./bookleaf.db"))
if (
    database_url.get_backend_name() == "sqlite"
    and database_url.database
    and database_url.database != ":memory:"
    and not Path(database_url.database).is_absolute()
):
    database_url = database_url.set(
        database=str((BACKEND_DIR / database_url.database).resolve())
    )
DATABASE_URL = database_url.render_as_string(hide_password=False)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
