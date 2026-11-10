import sqlite3
import pytest

import db
import typedefs

@pytest.fixture
def two_games(app, make_game):
    g1, _ = make_game("One")
    g2, _ = make_game("Two")
    with app.app_context():
        for account_id in ("alice", "bob"):
            db.create_account(typedefs.Account(id=account_id, name=account_id, email=account_id))
    return g1, g2

def test_account_can_join_multiple_games(app, two_games):
    g1, g2 = two_games
    with app.app_context():
        assert db.create_user(g1, "alice")
        assert db.create_user(g2, "alice")
        assert db.get_user_by_id(g1, "alice")
        assert db.get_user_by_id(g2, "alice")

def test_owner_is_set_per_game(app, two_games):
    g1, g2 = two_games
    with app.app_context():
        for g in (g1, g2):
            db.create_user(g, "alice")
            db.create_user(g, "bob")
        db.set_game_owner(g1, "alice")
        db.set_game_owner(g2, "bob")
        assert db.get_game_by_id(g1).owner == "alice"
        assert db.get_game_by_id(g2).owner == "bob"

def test_log_requires_member_of_that_game(app, two_games):
    g1, g2 = two_games
    with app.app_context():
        db.create_user(g1, "alice")
        db.create_user(g1, "bob")
        conn = db.get_db()
        conn.execute("INSERT INTO logs (game_id, user_id, target_id, msg_id) VALUES (?, 'alice', 'bob', 1)", (g1.bytes,))
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO logs (game_id, user_id, target_id, msg_id) VALUES (?, 'alice', 'bob', 1)", (g2.bytes,))

def test_removing_player_from_one_game_keeps_other(app, two_games):
    g1, g2 = two_games
    with app.app_context():
        db.create_user(g1, "alice")
        db.create_user(g2, "alice")
        db.remove_user(g2, "alice")
        assert db.get_user_by_id(g1, "alice")
        assert db.get_user_by_id(g2, "alice") is None
