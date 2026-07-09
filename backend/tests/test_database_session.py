import pytest
from sqlalchemy.engine import Engine

from app.db.session import create_database_engine, get_db


def test_create_database_engine_uses_given_url():
    engine = create_database_engine("sqlite+pysqlite:///:memory:")

    assert isinstance(engine, Engine)
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"


def test_get_db_closes_session(monkeypatch):
    created_sessions = []

    class FakeSession:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    def fake_session_local():
        session = FakeSession()
        created_sessions.append(session)
        return session

    monkeypatch.setattr("app.db.session.SessionLocal", fake_session_local)

    generator = get_db()
    yielded_session = next(generator)

    assert yielded_session is created_sessions[0]

    with pytest.raises(StopIteration):
        next(generator)

    assert created_sessions[0].closed is True

