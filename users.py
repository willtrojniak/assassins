import uuid
import flask
import db
import typedefs

def init_app(_: flask.Flask):
   pass 

class SignupError(Exception):
    pass

def signup(game_id: uuid.UUID, account_id: str) -> typedefs.User:
    user = db.get_user_by_id(game_id, account_id)
    if user:
        return user 

    game = db.get_game_by_id(game_id)
    if not game:
        raise SignupError("This game does not exist.")
    if game.started:
        raise SignupError("This game has already started.")

    success = db.create_user(game_id, account_id)
    if not success:
        raise SignupError("Something went wrong joining this game. Please try again.")

    user = db.get_user_by_id(game_id, account_id)
    if not user:
        raise SignupError("Something went wrong joining this game. Please try again.")

    db.set_game_owner(game_id, user.id)
    return user

