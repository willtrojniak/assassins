import flask
import click.testing

import db

def game_count(app) -> int:
    with app.app_context():
        return len(db.get_games())

def run_cli(app: flask.Flask, *args: str, input: str | None = None) -> click.testing.Result:
    # The flask CLI pushes an app context before running commands; the test runner does not
    with app.app_context():
        return app.test_cli_runner().invoke(args=list(args), input=input)

def run_init_db(app: flask.Flask, *args: str, input: str | None = None) -> click.testing.Result:
    return run_cli(app, "init-db", *args, input=input)

def test_init_db_aborts_without_confirmation(app, make_game):
    make_game("One")
    result = run_init_db(app, input="n\n")
    assert result.exit_code != 0
    assert game_count(app) == 1

def test_init_db_yes_recreates(app, make_game):
    make_game("One")
    result = run_init_db(app, "--yes")
    assert result.exit_code == 0, result.output
    assert game_count(app) == 0

def test_init_db_yes_recreates_after_games_are_played(app, make_game, player):
    _, url_id = make_game("One")
    alice, bob = player("alice"), player("bob")
    alice.post(f"/games/{url_id}/login")
    bob.post(f"/games/{url_id}/login")
    alice.post(f"/games/{url_id}/start")
    alice.post(f"/games/{url_id}/eliminate_user", data={"user_id": "bob", "elim_count": 1})

    result = run_init_db(app, "--yes")
    assert result.exit_code == 0, result.output
    assert game_count(app) == 0

def test_create_game_with_owner_email(app, player):
    player("alice")
    result = run_cli(app, "create-game", "One", "--owner", "ALICE@example.com")
    assert result.exit_code == 0, result.output
    with app.app_context():
        [game] = db.get_games()
    assert game.owner == "alice"

def test_create_game_with_unknown_owner_creates_nothing(app):
    result = run_cli(app, "create-game", "One", "--owner", "nobody@example.com")
    assert "No account with email 'nobody@example.com'" in result.output
    assert game_count(app) == 0

def test_create_game_without_owner_has_none(app):
    result = run_cli(app, "create-game", "One")
    assert result.exit_code == 0, result.output
    with app.app_context():
        [game] = db.get_games()
    assert game.owner is None
