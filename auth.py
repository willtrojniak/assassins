import datetime
import os
from dotenv.main import sys
import jwt

def create_bearer_token(user_id: int) -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        print("[ERROR] No JWT_SECRET set!", file=sys.stderr)
        return ""
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    return jwt.encode({'user_id': user_id, 'exp': exp}, secret, algorithm="HS256")

def read_bearer_token(token: str) -> int | None:
    try:
        secret = os.getenv("JWT_SECRET")
        if not secret:
            print("[ERROR] No JWT_SECRET set!", file=sys.stderr)
            return None
        res = jwt.decode(token, secret, algorithms="HS256")
        return res["user_id"]
    except:
        return None


