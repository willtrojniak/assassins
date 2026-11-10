import pytest

import db
import users

def test_joining_started_game_shows_reason(make_game, player):
    _, url_id = make_game("One")
    alice, bob, carol = player("alice"), player("bob"), player("carol")
    alice.post(f"/games/{url_id}/login")
    bob.post(f"/games/{url_id}/login")
    alice.post(f"/games/{url_id}/start")

    page = carol.post(f"/games/{url_id}/login", follow_redirects=True).data
    assert b"This game has already started." in page
    assert b"Welcome" not in page

def test_failed_insert_shows_retry_message(make_game, player, monkeypatch):
    _, url_id = make_game("One")
    alice = player("alice")
    monkeypatch.setattr(db, "create_user", lambda *_: False)

    page = alice.post(f"/games/{url_id}/login", follow_redirects=True).data
    assert b"Something went wrong joining this game. Please try again." in page

def test_signup_unknown_game_raises(app, make_game, player):
    game_id, _ = make_game("One")
    player("alice")
    with app.app_context():
        db.get_db().execute("DELETE FROM games")
        with pytest.raises(users.SignupError, match="does not exist"):
            users.signup(game_id, "alice")

def test_rejoining_is_not_an_error(make_game, player):
    _, url_id = make_game("One")
    alice = player("alice")
    alice.post(f"/games/{url_id}/login")

    page = alice.post(f"/games/{url_id}/login", follow_redirects=True).data
    assert b"Welcome, <i>Alice</i>" in page
    assert b"Something went wrong" not in page
