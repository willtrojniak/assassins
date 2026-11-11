import pytest

import db

@pytest.fixture
def organized_game(make_game, player):
    """A game organized by 'org', who does not play, with three players joined."""
    org = player("org")
    game_id, url_id = make_game("One", owner_id="org")
    clients = {name: player(name) for name in ("alice", "bob", "carol")}
    for client in clients.values():
        client.post(f"/games/{url_id}/login")
    return game_id, url_id, org, clients

def test_owner_does_not_have_to_play(app, organized_game):
    game_id, url_id, org, _ = organized_game

    page = org.get(f"/games/{url_id}").data.decode()
    assert "You are organizing this game" in page
    assert "Start Game" in page
    assert "Your target is" not in page

    org.post(f"/games/{url_id}/start")
    with app.app_context():
        assert db.get_game_by_id(game_id).started
        assert db.get_game_by_id(game_id).owner == "org"
        assert db.get_user_by_id(game_id, "org") is None
        assert {u.target_user_id for u in db.get_users_by_game(game_id)} == {"alice", "bob", "carol"}

def test_owner_can_announce_and_eliminate(app, organized_game):
    game_id, url_id, org, _ = organized_game
    org.post(f"/games/{url_id}/announcement", data={"msg": "Rules: no headshots"})
    org.post(f"/games/{url_id}/start")
    org.post(f"/games/{url_id}/eliminate_user", data={"user_id": "alice", "elim_count": 1})

    with app.app_context():
        assert db.get_game_by_id(game_id).announcement == "Rules: no headshots"
        assert db.get_user_by_id(game_id, "alice").eliminated

def test_players_are_not_owners(organized_game):
    _, url_id, _, clients = organized_game
    assert "Start Game" not in clients["alice"].get(f"/games/{url_id}").data.decode()
    assert clients["alice"].post(f"/games/{url_id}/start").status_code == 403

def test_first_joiner_is_owner_when_none_set(app, make_game, player):
    game_id, url_id = make_game("One")
    player("alice").post(f"/games/{url_id}/login")
    with app.app_context():
        assert db.get_game_by_id(game_id).owner == "alice"

def test_owner_who_plays_can_be_removed(app, make_game, player):
    game_id, url_id = make_game("One")
    alice, bob = player("alice"), player("bob")
    alice.post(f"/games/{url_id}/login")
    bob.post(f"/games/{url_id}/login")

    alice.post(f"/games/{url_id}/delete_user", data={"user_id": "alice"})
    with app.app_context():
        assert db.get_user_by_id(game_id, "alice") is None
        assert db.get_game_by_id(game_id).owner == "alice"
    assert "You are organizing this game" in alice.get(f"/games/{url_id}").data.decode()

def test_home_lists_organized_games(organized_game, player):
    _, _, org, _ = organized_game
    page = org.get("/").data.decode()
    assert "One" in page
    assert "Organizer" in page
    assert "3 / 3" in page

@pytest.mark.parametrize("path", ["start", "announcement", "delete_user", "eliminate_user"])
def test_owner_only_routes_forbid_others(organized_game, app, path):
    _, url_id, _, clients = organized_game
    assert clients["alice"].post(f"/games/{url_id}/{path}", data={"user_id": "bob"}).status_code == 403
    assert app.test_client().post(f"/games/{url_id}/{path}", data={"user_id": "bob"}).status_code == 403

def test_register_requires_login(make_game, app):
    _, url_id = make_game("One")
    assert app.test_client().post(f"/games/{url_id}/login").status_code == 401
