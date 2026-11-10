import flask
import click.testing

import db

def game_count(app) -> int:
    with app.app_context():
        return len(db.get_games())

def run_init_db(app: flask.Flask, *args: str, input: str | None = None) -> click.testing.Result:
    # The flask CLI pushes an app context before running commands; the test runner does not
    with app.app_context():
        return app.test_cli_runner().invoke(args=["init-db", *args], input=input)

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
