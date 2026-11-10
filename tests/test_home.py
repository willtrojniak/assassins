import re

def home_rows(client) -> dict[str, list[str]]:
    """Map each game name on the home page to the text of its other cells."""
    html = client.get("/").data.decode()
    rows = re.findall(r"<tr.*?>(.*?)</tr>", html, re.DOTALL)
    result = {}
    for row in rows:
        cells = [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td.*?>(.*?)</td>", row, re.DOTALL)]
        result[cells[0]] = cells[1:]
    return result

def test_logged_out_shows_login(app):
    page = app.test_client().get("/").data
    assert b"Log In" in page
    assert b'action="/auth"' in page
    assert b"My Games" not in page

def test_no_games_shows_empty_state(player):
    page = player("alice").get("/").data.decode()
    assert "My Games" in page
    assert "You haven't joined any games yet" in page

def test_lists_joined_games_with_status(make_game, player):
    _, one = make_game("One")
    _, two = make_game("Two")
    _, three = make_game("Three")
    _, other = make_game("Not Mine")
    alice, bob, carol = player("alice"), player("bob"), player("carol")

    alice.post(f"/games/{one}/login")

    alice.post(f"/games/{two}/login")
    bob.post(f"/games/{two}/login")
    alice.post(f"/games/{two}/start")

    bob.post(f"/games/{three}/login")
    alice.post(f"/games/{three}/login")
    carol.post(f"/games/{three}/login")
    bob.post(f"/games/{three}/start")
    bob.post(f"/games/{three}/eliminate_user", data={"user_id": "alice", "elim_count": 1})

    bob.post(f"/games/{other}/login")

    # status, remaining
    assert home_rows(alice) == {
        "One": ["Not started", "1 / 1"],
        "Three": ["Eliminated", "2 / 3"],
        "Two": ["Alive", "2 / 2"],
    }
    page = alice.get("/").data.decode()
    for url_id in (one, two, three):
        assert f'href="/games/{url_id}"' in page
