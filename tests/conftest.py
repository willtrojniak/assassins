import os
import uuid
import pytest
import flask
import flask.testing

import app as app_module
import auth
import db
import typedefs
import util

@pytest.fixture
def app(tmp_path, monkeypatch) -> flask.Flask:
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    app = app_module.create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "data" / "db.sqlite"),
    })
    os.makedirs(tmp_path / "data")
    with app.app_context():
        db.init_db(db.get_db())
    return app

@pytest.fixture
def make_game(app: flask.Flask):
    def make(name: str) -> tuple[uuid.UUID, str]:
        with app.app_context():
            game_id = db.create_game(name)
        assert game_id
        return game_id, util.uuid_to_str(game_id)
    return make

@pytest.fixture
def player(app: flask.Flask):
    """Create an account and return a test client logged in as it."""
    def make(account_id: str) -> flask.testing.FlaskClient:
        with app.app_context():
            db.create_account(typedefs.Account(id=account_id, name=account_id.title(), email=f"{account_id}@example.com"))
        client = app.test_client()
        client.set_cookie("jwt_cookie", auth.create_bearer_token(account_id))
        return client
    return make
