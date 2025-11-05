import datetime
import jwt

def create_bearer_token(user_id: int) -> str:
    # FIXME: Load secret from env
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    return jwt.encode({'user_id': user_id, 'exp': exp}, "SUPER_SECRET", algorithm="HS256")

def read_bearer_token(token: str) -> int | None:
    try:
        res = jwt.decode(token, "SUPER_SECRET", algorithms="HS256")
        return res["user_id"]
    except:
        return None


