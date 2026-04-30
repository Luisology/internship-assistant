"""Local demo authentication.

⚠️  This is a local demo authentication system intended for personal
local use only. It is NOT production-grade auth. There is no email
verification, no rate limiting, no account recovery, no MFA. For a
hosted deployment, plug in a real auth provider.

Storage: data/users.json — a JSON list of user records:
  {
    "name":          str,
    "email":         str (lowercased on save),
    "salt":          hex string (16 bytes),
    "password_hash": hex string (PBKDF2-SHA256, 200k iters, 32 bytes),
    "created_at":    ISO 8601 UTC timestamp,
  }

Passwords are NEVER stored in plaintext. Hashes are compared in
constant time via hmac.compare_digest.
"""

import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone

USERS_FILE = os.path.join("data", "users.json")
PBKDF2_ITERS = 200_000
SALT_BYTES = 16
HASH_BYTES = 32
MIN_PASSWORD_LEN = 8
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ── Storage ──────────────────────────────────────────────────────────────────

def load_users(path=USERS_FILE):
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_users(users, path=USERS_FILE):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w") as f:
        json.dump(users, f, indent=2)


# ── Hashing ──────────────────────────────────────────────────────────────────

def hash_password(password, salt=None):
    """Return (salt_hex, hash_hex). Generates a fresh salt unless one is given."""
    if salt is None:
        salt_bytes = os.urandom(SALT_BYTES)
    else:
        salt_bytes = bytes.fromhex(salt) if isinstance(salt, str) else salt
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                             salt_bytes, PBKDF2_ITERS, dklen=HASH_BYTES)
    return salt_bytes.hex(), h.hex()


def verify_password(password, salt_hex, expected_hash_hex):
    _, computed_hex = hash_password(password, salt=salt_hex)
    # constant-time comparison
    return hmac.compare_digest(computed_hex, expected_hash_hex)


# ── Lookup ───────────────────────────────────────────────────────────────────

def find_user(email, users):
    target = (email or "").strip().lower()
    for u in users:
        if (u.get("email") or "").strip().lower() == target:
            return u
    return None


# ── Validation ───────────────────────────────────────────────────────────────

def validate_email(email):
    return bool(EMAIL_RE.match((email or "").strip()))


def validate_password(password):
    if not password or len(password) < MIN_PASSWORD_LEN:
        return f"Password must be at least {MIN_PASSWORD_LEN} characters."
    return None


# ── Register / Authenticate ──────────────────────────────────────────────────

def register(name, email, password, confirm_password, path=USERS_FILE):
    """Register a new user. Returns (success, error_or_user)."""
    name = (name or "").strip()
    email = (email or "").strip().lower()

    if not name:
        return False, "Name is required."
    if not validate_email(email):
        return False, "Please enter a valid email address."
    pw_err = validate_password(password)
    if pw_err:
        return False, pw_err
    if password != confirm_password:
        return False, "Passwords do not match."

    users = load_users(path)
    if find_user(email, users):
        return False, "An account with this email already exists. Try signing in."

    salt_hex, hash_hex = hash_password(password)
    user = {
        "name": name,
        "email": email,
        "salt": salt_hex,
        "password_hash": hash_hex,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    users.append(user)
    save_users(users, path)
    return True, user


def authenticate(email, password, path=USERS_FILE):
    """Return (success, user_or_error_message)."""
    users = load_users(path)
    user = find_user(email, users)
    if not user:
        return False, "No account found for this email."
    if not verify_password(password, user.get("salt", ""), user.get("password_hash", "")):
        return False, "Incorrect password."
    return True, user


# ── Helpers used by the UI ───────────────────────────────────────────────────

def public_user(user):
    """Strip secrets before storing in session_state. Always use this."""
    if not user:
        return None
    return {
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "is_guest": False,
    }


def guest_user():
    return {"name": "Guest", "email": "", "is_guest": True}
