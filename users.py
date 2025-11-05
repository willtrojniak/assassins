import uuid
import db
import typedefs
import util 

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

