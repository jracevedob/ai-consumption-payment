from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Cookie, Depends, HTTPException, Response

from .db import connect, get_session, get_user_by_id


SESSION_COOKIE = "acp_session"
SESSION_TTL_HOURS = 24 * 7


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str, salt: str) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return dk.hex()


def new_salt() -> str:
    return secrets.token_urlsafe(16)


def new_session_id() -> str:
    return secrets.token_urlsafe(24)


def session_expiry_iso() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=SESSION_TTL_HOURS)).isoformat()


def set_session_cookie(resp: Response, session_id: str) -> None:
    resp.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        secure=False,  # set True behind HTTPS
        samesite="lax",
        path="/",
        max_age=SESSION_TTL_HOURS * 3600,
    )


def clear_session_cookie(resp: Response) -> None:
    resp.delete_cookie(key=SESSION_COOKIE, path="/")


def require_user(session_id: Optional[str] = Cookie(default=None, alias=SESSION_COOKIE)):
    if not session_id:
        raise HTTPException(status_code=401, detail="not authenticated")

    con = connect()
    sess = get_session(con, session_id)
    if sess is None:
        raise HTTPException(status_code=401, detail="invalid session")

    # Basic expiry check (iso strings sort lexicographically for same format)
    if str(sess["expires_at"]) < now_iso():
        raise HTTPException(status_code=401, detail="session expired")

    user = get_user_by_id(con, int(sess["user_id"]))
    if user is None:
        raise HTTPException(status_code=401, detail="user not found")

    return {"id": int(user["id"]), "email": str(user["email"])}


CurrentUser = Depends(require_user)

