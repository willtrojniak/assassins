import html
import re

import db

def confirm_forms(client, game: str) -> dict[str, dict[str, str]]:
    """Map each confirm-guarded form's title to its data-confirm-* attributes."""
    page = client.get(f"/games/{game}").data.decode()
    result = {}
    for attrs in re.findall(r"<form[^>]*?(data-confirm-.*?)>", page, re.DOTALL):
        fields = {k: html.unescape(v) for k, v in re.findall(r'data-confirm-(\w+)="(.*?)"', attrs)}
        result[fields["title"]] = fields
    return result

def test_remove_confirm_before_start(make_game, player):
    _, game = make_game("Game")
    alice, bob = player("alice"), player("bob")
    alice.post(f"/games/{game}/login")
    bob.post(f"/games/{game}/login")

    forms = confirm_forms(alice, game)
    assert forms["Remove Bob from the game?"] == {
        "title": "Remove Bob from the game?",
        "body": "They can rejoin before the game starts.",
        "label": "Remove",
        "variant": "neutral",
    }
    assert 'id="confirm-dialog"' in alice.get(f"/games/{game}").data.decode()

def test_eliminate_and_forfeit_confirm_name_assassin(app, make_game, player):
    game_id, game = make_game("Game")
    alice, bob, carol = player("alice"), player("bob"), player("carol")
    for p in (alice, bob, carol):
        p.post(f"/games/{game}/login")
    alice.post(f"/games/{game}/start")

    with app.app_context():
        users = db.get_users_by_game(game_id)
    names = {u.id: u.name for u in users}
    assassin_of = {u.target_user_id: names[u.id] for u in users}

    forms = confirm_forms(alice, game)
    assert not any(f["title"].startswith("Remove") for f in forms.values())
    for u in users:
        assert forms[f"Eliminate {u.name}?"] == {
            "title": f"Eliminate {u.name}?",
            "body": f"{assassin_of[u.id]} will be credited with the kill and receive {u.name}'s target.",
            "label": "Eliminate",
            "variant": "danger",
        }
        assert forms[f"Forfeit {u.name}?"] == {
            "title": f"Forfeit {u.name}?",
            "body": f"{assassin_of[u.id]} will receive {u.name}'s target but won't be credited with a kill.",
            "label": "Forfeit",
            "variant": "neutral",
        }

def test_eliminated_player_has_no_confirm(make_game, player):
    _, game = make_game("Game")
    alice, bob, carol = player("alice"), player("bob"), player("carol")
    for p in (alice, bob, carol):
        p.post(f"/games/{game}/login")
    alice.post(f"/games/{game}/start")
    alice.post(f"/games/{game}/eliminate_user", data={"user_id": "carol", "elim_count": 1})

    forms = confirm_forms(alice, game)
    assert "Eliminate Carol?" not in forms
    assert "Forfeit Carol?" not in forms
    assert "Eliminate Bob?" in forms

def test_non_owner_has_no_dialog(make_game, player):
    _, game = make_game("Game")
    alice, bob = player("alice"), player("bob")
    alice.post(f"/games/{game}/login")
    bob.post(f"/games/{game}/login")

    page = bob.get(f"/games/{game}").data.decode()
    assert 'id="confirm-dialog"' not in page
    assert "data-confirm-" not in page

def test_non_playing_organizer_gets_dialog(make_game, player):
    org = player("org")
    _, game = make_game("Game", owner_id="org")
    for name in ("alice", "bob"):
        player(name).post(f"/games/{game}/login")

    page = org.get(f"/games/{game}").data.decode()
    assert "data-confirm-title" in page
    assert 'id="confirm-dialog"' in page
