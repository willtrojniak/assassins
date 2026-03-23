import click
import flask
import uuid
import auth
import db

import typedefs
import users
import util

bp = flask.Blueprint('game', __name__)


def create_game(name: str) -> uuid.UUID | None:
    return db.create_game(name)

@bp.get("/")
def root_handler():
    return flask.render_template('./index.html')

@click.command('create-game')
@click.argument('name')
def create_game_cmd(name: str):
    game_id = create_game(name)
    if not game_id:
        click.echo("Failed to create game", err=True)
        return

    click.echo(util.uuid_to_str(game_id))

@click.command('reset-game')
@click.argument('id')
def reset_game_cmd(id: str):
    game_id = util.str_to_uuid(id)
    if not game_id:
        click.echo("Invalid game id", err=True)
        return
    db.reset_game(game_id)

# @bp.post("/games")
# def create_game_handler():
#     game_name = flask.request.form["name"]
#     game_id = create_game(game_name)
#     if not game_id:
#         flask.flash("Failed to create game. Please try again.")
#         return flask.redirect('/')
#
#     url_id = util.uuid_to_str(game_id)
#
#     return flask.redirect(f"/games/{url_id}")

@bp.get("/games/<game_id_param>")
def get_game_handler(game_id_param: str):
    game_id = util.str_to_uuid(game_id_param)
    if not game_id:
        flask.abort(404)
    game = db.get_game_by_id(game_id)
    users = db.get_users_by_game(game_id)
    if not game:
        flask.abort(404)

    token = flask.request.cookies.get("jwt_cookie")
    account_id : str | None = None
    user: typedefs.User | None = None
    target: typedefs.User | None = None

    if token:
        account_id = auth.read_bearer_token(token)
        if account_id:
            user = db.get_user_by_id(game_id, account_id)
            if user and user.target_user_id:
                target = db.get_user_by_id(game_id, user.target_user_id)

    print("Target: ", target)

    logs = db.get_game_logs(game_id)

    return flask.render_template('./game.html', 
                                 id=game_id_param, 
                                 game=game,
                                 account_id=account_id,
                                 users=users,
                                 user=user,
                                 target=target,
                                 logs=logs)
    

@bp.post("/games/<game_id_param>/login")
def login_post_handler(game_id_param: str):
    game_id = util.str_to_uuid(game_id_param)
    if not game_id:
        flask.abort(404)
    response = flask.make_response(flask.redirect(flask.url_for('game.get_game_handler', game_id_param=game_id_param)))

    token = flask.request.cookies.get("jwt_cookie")
    account_id: str | None = None
    if token:
        account_id = auth.read_bearer_token(token)

    if (not account_id):
        flask.abort(201, "Unauthorized to register")

    user = users.signup(game_id, account_id)
    if not user:
        flask.flash("Sign in failed.", "sign-in")
        return response

    return response

@bp.post("/games/<game_id_param>/start")
def start_game_handler(game_id_param: str):
    game_id = util.str_to_uuid(game_id_param)
    if not game_id:
        flask.abort(404)

    game = db.get_game_by_id(game_id)
    if not game:
        flask.abort(404)
    users = db.get_users_by_game(game_id)

    response = flask.make_response(flask.redirect(flask.url_for('game.get_game_handler', game_id_param=game_id_param)))

    token = flask.request.cookies.get("jwt_cookie")
    user: typedefs.User | None = None

    if token:
        user_id = auth.read_bearer_token(token)
        if user_id:
            user = db.get_user_by_id(game_id, user_id)

    if (not user) or user.id != game.owner:
        flask.abort(201, "Unauthorized to start game")


    print(f"Starting game '{game.name}'...")
    mapping = util.gen_target_maps([user.id for user in users])
    db.set_user_targets(game_id, mapping)

    return response

@bp.post("/games/<game_id_param>/announcement")
def set_announcement_handler(game_id_param: str):
    game_id = util.str_to_uuid(game_id_param)
    if not game_id:
        flask.abort(404)
    game = db.get_game_by_id(game_id)
    if not game:
        flask.abort(404)

    msg = flask.request.form.get("msg",None,type=str)
    response = flask.make_response(flask.redirect(flask.url_for('game.get_game_handler', game_id_param=game_id_param)))

    token = flask.request.cookies.get("jwt_cookie")
    user: typedefs.User | None = None

    if token:
        user_id = auth.read_bearer_token(token)
        if user_id:
            user = db.get_user_by_id(game_id, user_id)

    if (not user) or user.id != game.owner:
        flask.abort(201, "Unauthorized to set game announcement")


    db.set_game_announcement(game_id, msg)
    return response

@bp.post("/games/<game_id_param>/delete_user")
def remove_user_handler(game_id_param: str):
    game_id = util.str_to_uuid(game_id_param)
    if not game_id:
        flask.abort(404)

    target_user_id = flask.request.form.get("user_id","",type=str)
    game = db.get_game_by_id(game_id)
    if not game:
        flask.abort(404)

    response = flask.make_response(flask.redirect(flask.url_for('game.get_game_handler', game_id_param=game_id_param)))

    token = flask.request.cookies.get("jwt_cookie")
    user: typedefs.User | None = None

    if token:
        user_id = auth.read_bearer_token(token)
        if user_id:
            user = db.get_user_by_id(game_id, user_id)

    if game.started or (not user) or user.id != game.owner:
        flask.abort(201, "Unauthorized to remove player")


    db.remove_user(game_id, target_user_id)
    return response

@bp.post("/games/<game_id_param>/eliminate_user")
def eliminate_user_target_handler(game_id_param: str):
    game_id = util.str_to_uuid(game_id_param)
    if not game_id:
        flask.abort(404)

    target_user_id = flask.request.form.get("user_id","",type=str)
    elim_count = flask.request.form.get("elim_count",0,type=int)
    game = db.get_game_by_id(game_id)
    if not game:
        flask.abort(404)

    response = flask.make_response(flask.redirect(flask.url_for('game.get_game_handler', game_id_param=game_id_param)))

    token = flask.request.cookies.get("jwt_cookie")
    user: typedefs.User | None = None

    if token:
        user_id = auth.read_bearer_token(token)
        if user_id:
            user = db.get_user_by_id(game_id, user_id)

    if (not game.started) or (not user) or user.id != game.owner:
        flask.abort(201, "Unauthorized to eliminate player")


    db.eliminate_user(game_id, target_user_id, elim_count)
    return response
