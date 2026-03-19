import uuid
import flask
import db
import typedefs

def init_app(_: flask.Flask):
   pass 

def signup(game_id: uuid.UUID, account_id: str) -> typedefs.User | None:
    user = db.get_user_by_id(game_id, account_id)
    if user:
        return user 

    game = db.get_game_by_id(game_id)
    if not game or game.started:
        return None

    success = db.create_user(game_id, account_id)
    if not success:
        return None


    user = db.get_user_by_id(game_id, account_id)
    if not user:
        return None

    db.set_game_owner(game_id, user.id)
    return user

