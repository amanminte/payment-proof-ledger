"""User Authentication & Role-Based Access Control (RBAC).

Features:
- Parameterized SQLite queries (defends against SQL injection)
- Cryptographic password hashing with salted PBKDF2/Scrypt via Werkzeug
- Role enforcement: 'owner' vs 'cashier'
- Ephemeral 10-minute expiring passcodes for cashier shift accounting (FR-10)
"""
from datetime import timedelta
import re
import secrets
from werkzeug.security import check_password_hash, generate_password_hash

from . import config, db
from .timeutil import iso, now_utc, parse

USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_]{3,30}$")


def validate_username(username):
    username = (username or "").strip()
    if not USERNAME_REGEX.match(username):
        raise ValueError("Username must be 3-30 letters, numbers, or underscores.")
    return username


def validate_password(password):
    password = password or ""
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    return password


def create_user(username, password, role="cashier"):
    """Register a new user with a salted & hashed password."""
    username = validate_username(username)
    password = validate_password(password)
    role = role.lower().strip()
    if role not in ("owner", "cashier"):
        raise ValueError("Role must be either 'owner' or 'cashier'.")

    password_hash = generate_password_hash(password)
    now = iso(now_utc())

    with db.connect() as conn:
        existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            raise ValueError(f"Username '{username}' is already taken.")
        user_id = conn.execute(
            "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
            (username, password_hash, role, now),
        ).lastrowid
        return {"id": user_id, "username": username, "role": role}


def authenticate(username, password):
    """Authenticate credentials against salted hash. Returns user dict or None."""
    username = (username or "").strip()
    password = password or ""
    with db.connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not user:
            return None
        if not check_password_hash(user["password_hash"], password):
            return None
        return dict(user)


def get_user_by_id(user_id):
    """Retrieve user record by ID."""
    if not user_id:
        return None
    with db.connect() as conn:
        user = conn.execute("SELECT id, username, role, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(user) if user else None


def count_users():
    """Return total number of registered users."""
    with db.connect() as conn:
        return conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]


def seed_default_users():
    """Ensure baseline test accounts exist for evaluator demo only when DEMO_MODE=1."""
    if not config.DEMO_MODE:
        return
    with db.connect() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        if count == 0:
            now = iso(now_utc())
            conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, 'owner', ?)",
                ("owner", generate_password_hash("owner123"), now),
            )
            conn.execute(
                "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, 'cashier', ?)",
                ("cashier", generate_password_hash("cashier123"), now),
            )


# ---------------------------------------------------------------------------
# Ephemeral 10-Minute Accounting Passcodes (FR-10)
# ---------------------------------------------------------------------------

def generate_ephemeral_passcode(created_by=None, ttl_minutes=10, now=None):
    """Generate a cryptographically secure 6-digit numeric passcode expiring in `ttl_minutes`.
    
    Invalidates previous unused passcodes so only the newest active code is valid.
    """
    start = now if now is not None else now_utc()
    expiry = start + timedelta(minutes=ttl_minutes)
    created_at = iso(start)
    expires_at = iso(expiry)

    # 6-digit zero-padded number e.g. '048291'
    token = f"{secrets.randbelow(1_000_000):06d}"

    with db.connect() as conn:
        conn.execute("UPDATE access_tokens SET is_used = 1 WHERE is_used = 0")
        conn.execute(
            "INSERT INTO access_tokens (token, created_by, created_at, expires_at, is_used) VALUES (?, ?, ?, ?, 0)",
            (token, created_by, created_at, expires_at),
        )
    return {
        "token": token,
        "created_by": created_by,
        "created_at": created_at,
        "expires_at": expires_at,
        "ttl_minutes": ttl_minutes,
    }


def get_active_passcode(now=None):
    """Return the currently valid, unexpired, and unused passcode dict, or None."""
    current = now if now is not None else now_utc()
    now_str = iso(current)
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM access_tokens WHERE is_used = 0 AND expires_at > ? ORDER BY id DESC LIMIT 1",
            (now_str,),
        ).fetchone()
        if not row:
            return None
        res = dict(row)
        exp = parse(res["expires_at"])
        res["remaining_seconds"] = max(0, int((exp - current).total_seconds()))
        return res


def verify_and_consume_passcode(passcode, now=None):
    """Verify entered passcode. If valid and not expired, mark as used and return success."""
    code = (passcode or "").strip().replace(" ", "")
    if not code or len(code) != 6 or not code.isdigit():
        return {"ok": False, "error": "Passcode must be a 6-digit number."}

    current = now if now is not None else now_utc()
    now_str = iso(current)
    with db.connect() as conn:
        row = conn.execute(
            "SELECT * FROM access_tokens WHERE token = ? AND is_used = 0 AND expires_at > ?",
            (code, now_str),
        ).fetchone()
        if not row:
            return {"ok": False, "error": "Invalid or expired passcode. Request a new code from the Shop Owner."}

        conn.execute("UPDATE access_tokens SET is_used = 1 WHERE id = ?", (row["id"],))
        return {
            "ok": True,
            "token": row["token"],
            "expires_at": row["expires_at"],
        }


def revoke_all_passcodes(created_by=None):
    """Revoke any active passcodes immediately."""
    with db.connect() as conn:
        if created_by:
            conn.execute("UPDATE access_tokens SET is_used = 1 WHERE created_by = ? AND is_used = 0", (created_by,))
        else:
            conn.execute("UPDATE access_tokens SET is_used = 1 WHERE is_used = 0")
