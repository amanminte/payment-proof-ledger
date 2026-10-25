import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file():
    """Tiny .env loader so no extra package is needed."""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_env_file()

DEMO_MODE = os.environ.get("DEMO_MODE", "0").strip().lower() in ("1", "true", "yes")
ENABLE_SIMULATOR = os.environ.get("ENABLE_SIMULATOR", "1" if DEMO_MODE else "0").strip().lower() in ("1", "true", "yes")
HOST = os.environ.get("HOST", "127.0.0.1")

SMS_TOKEN = os.environ.get("SMS_TOKEN", "change-me")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
DATABASE = os.environ.get("DATABASE", str(BASE_DIR / "ppl.db"))
ACCOUNTING_PASSCODE_TTL_MIN = int(os.environ.get("ACCOUNTING_PASSCODE_TTL_MIN", "10"))


def validate_secrets():
    """Refuse to run in production mode if default or weak placeholder secrets are used."""
    if not DEMO_MODE:
        for name, val in (("SECRET_KEY", SECRET_KEY), ("SMS_TOKEN", SMS_TOKEN)):
            if not val or val == "change-me":
                raise RuntimeError(
                    f"Security Failure: Refusing to start with default {name}='change-me'. "
                    "Set strong keys in .env or run with DEMO_MODE=1 for evaluation only."
                )
            if len(val) < 32:
                raise RuntimeError(
                    f"Security Failure: {name} is too short ({len(val)} chars). "
                    "Production keys must be at least 32 characters long. "
                    'Generate one via: python -c "import secrets; print(secrets.token_hex(32))"'
                )
            if val.lower().startswith("generate-a"):
                raise RuntimeError(
                    f"Security Failure: {name} uses placeholder text from .env.example. "
                    'Generate a real random secret via: python -c "import secrets; print(secrets.token_hex(32))"'
                )

# Alert timing (minutes after a sale is opened)
YELLOW_AFTER_MIN = 2
RED_AFTER_MIN = 10
# A payment that arrives BEFORE the sale is opened can still be matched
# if it arrived at most this many minutes earlier.
UNASSIGNED_WINDOW_MIN = 10

MAX_AMOUNT = 1_000_000
TZ_OFFSET_HOURS = 3  # Addis Ababa (UTC+3), used for daily/weekly/monthly reports
