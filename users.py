import uuid
import click
import flask
import db
import typedefs
import util 

def init_app(app: flask.Flask):
    app.cli.add_command(overwrite_password_cmd)

def signup_or_login(game_id: uuid.UUID, username: str, password: str) -> typedefs.User | None:
    pwd: bytes = password.encode()

    user = db.get_user_by_username(game_id, username)
    if user:
        return user if util.check_pwd(pwd, user.password_hash) else None

    game = db.get_game_by_id(game_id)
    if not game or game.started:
        return None

    success = db.create_user(game_id, username, util.hash_pwd(pwd))
    if not success:
        return None


    user = db.get_user_by_username(game_id, username)
    if not user:
        return None

    db.set_game_owner(game_id, user.id)
    return user

def overwrite_password(game_id: uuid.UUID, username: str, password: str) -> bool:
    pwd_hash = util.hash_pwd(password.encode())
    return db.update_user_pwd(game_id, username, pwd_hash)


@click.command('set-password')
@click.argument('game_id')
@click.argument('username')
@click.argument('new_password')
def overwrite_password_cmd(game_id: str, username: str, new_password: str):
    id = util.str_to_uuid(game_id)
    if not id:
        click.echo("Invalid game_id", err=True)
        return

    if overwrite_password(id, username, new_password):
        click.echo("Successfully updated password", err=True)
    else:
        click.echo("Failed to update password", err=True)


