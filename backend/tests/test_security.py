from datetime import timedelta

import jwt
import pytest

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_creates_verifiable_hash():
    password_hash = hash_password("correct-password")

    assert password_hash != "correct-password"
    assert verify_password("correct-password", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_access_token_can_be_created_and_decoded():
    settings = Settings(
        jwt_secret_key="test-secret-key-with-more-than-32-bytes",
        jwt_access_token_expire_minutes=30,
    )

    token = create_access_token("42", settings)
    payload = decode_access_token(token, settings)

    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_expired_access_token_is_rejected():
    settings = Settings(
        jwt_secret_key="test-secret-key-with-more-than-32-bytes",
        jwt_access_token_expire_minutes=30,
    )
    token = create_access_token("42", settings, expires_delta=timedelta(minutes=-1))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token, settings)
