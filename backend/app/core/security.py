import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

ALGORITHM = "HS256"
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=64,
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "scrypt":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def create_access_token(
    subject: str,
    secret_key: str,
    expires_minutes: int,
) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    return jwt.encode(
        {"sub": subject, "exp": expires_at},
        secret_key,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str, secret_key: str) -> str | None:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        return subject if isinstance(subject, str) else None
    except JWTError:
        return None
