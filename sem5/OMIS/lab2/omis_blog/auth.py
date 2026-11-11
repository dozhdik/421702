"""Local authentication, registration, and access permissions."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import re
import sqlite3

from omis_blog import domain as d
from omis_blog.storage import Database


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


DUMMY_PASSWORD_HASH = hash_password("not-a-real-account", "00" * 16)


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, digest = stored.split("$", 2)
        return hmac.compare_digest(hash_password(password, salt).split("$")[-1], digest)
    except ValueError:
        return False


def authenticate(db: Database, login: str, password: str) -> d.UserAccount | None:
    accounts = db.list_entities(d.UserAccount, 'lower(login)=?', (login.strip().lower(),))
    if not accounts or not accounts[0].is_active:
        verify_password(password, DUMMY_PASSWORD_HASH)
        return None
    return accounts[0] if verify_password(password, accounts[0].password_hash) else None


def register_author(db: Database, full_name: str, login: str, password: str,
                    confirmation: str) -> d.UserAccount:
    full_name = " ".join(full_name.split())
    login = login.strip().lower()
    if not 2 <= len(full_name) <= 120:
        raise d.DomainException("invalid_full_name")
    if not re.fullmatch(r"[a-z0-9_.-]{3,40}", login):
        raise d.DomainException("invalid_login")
    if not 10 <= len(password) <= 128:
        raise d.DomainException("invalid_password_length")
    if password != confirmation:
        raise d.DomainException("password_mismatch")
    if db.list_entities(d.UserAccount, 'lower(login)=?', (login,)):
        raise d.DomainException("login_taken")
    role_row = db.connection.execute("""
        SELECT r.role_id FROM Role r
        JOIN AccessPermission p ON p.role_id=r.role_id AND p.operation_code='article.write'
        WHERE NOT EXISTS (SELECT 1 FROM AccessPermission x WHERE x.role_id=r.role_id
            AND x.operation_code IN ('article.moderate','admin')) LIMIT 1
    """).fetchone()
    author_role = role_row[0] if role_row else d.new_id()
    user = d.User(full_name=full_name)
    password_hash = hash_password(password)
    account = d.UserAccount(login=login, password_hash=password_hash,
                            user_id=user.user_id, role_id=author_role)
    user.account_id = account.account_id
    user.password_hash = password_hash
    try:
        with db.connection:
            if not role_row:
                db.save(d.Role(role_id=author_role, role_name="Author", description="Content author"), commit=False)
            for operation in ("article.write", "feed.read", "comment.write", "reaction.write"):
                existing = db.list_entities(d.AccessPermission, 'role_id=? AND operation_code=?',
                                            (author_role, operation))
                if not existing:
                    db.save(d.AccessPermission(operation_code=operation, role_id=author_role), commit=False)
            db.save(user, commit=False)
            db.save(account, commit=False)
            db.save(d.ContentAuthor(full_name=full_name, user_id=user.user_id), commit=False)
            db.save(d.Reader(full_name=full_name, user_id=user.user_id), commit=False)
    except sqlite3.IntegrityError as exc:
        raise d.DomainException("login_taken") from exc
    return account


def role(db: Database, account: d.UserAccount | None) -> str:
    if account is None:
        return ""
    obj = db.get(d.Role, account.role_id)
    return obj.role_name if obj else ""


def has_permission(db: Database, account: d.UserAccount | None, operation: str) -> bool:
    if account is None or not account.is_active:
        return False
    return bool(db.list_entities(d.AccessPermission, 'role_id=? AND operation_code=?',
                          (account.role_id, operation)))
