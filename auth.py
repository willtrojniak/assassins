import datetime
import os
import sys
import jwt
import jwt.algorithms
import secrets
import flask
import werkzeug.exceptions
import requests
import functools
import db
from typedefs import Account

AUTH_SCOPE = "openid profile email"

def create_bearer_token(user_id: str) -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        print("[ERROR] No JWT_SECRET set!", file=sys.stderr)
        return ""
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    return jwt.encode({'user_id': user_id, 'exp': exp}, secret, algorithm="HS256")

def read_bearer_token(token: str) -> str | None:
    try:
        secret = os.getenv("JWT_SECRET")
        if not secret:
            print("[ERROR] No JWT_SECRET set!", file=sys.stderr)
            return None
        res = jwt.decode(token, secret, algorithms="HS256")
        return res["user_id"]
    except:
        return None

bp = flask.Blueprint('auth', __name__)

@functools.cache
def oidc_get_discovery():
    return requests.get(os.getenv("OIDC_DISCOVERY_URL", "<NONE>")).json()

@functools.cache
def oidc_issuer() -> str:
    return oidc_get_discovery()["issuer"]

@functools.cache
def oidc_auth_endpoint() -> str:
    return oidc_get_discovery()["authorization_endpoint"]

@functools.cache
def oidc_token_endpoint() -> str:
    return oidc_get_discovery()["token_endpoint"]

@functools.cache
def oidc_jwks_endpoint() -> str:
    return oidc_get_discovery()["jwks_uri"]

@bp.post("/auth")
def oauth_begin():
    state = secrets.token_urlsafe(16)
    flask.session["state"] = state
    nonce = secrets.token_urlsafe(16)

    cb = flask.request.form.get("cb", "", type=str)
    flask.session["cb"] = cb
    
    auth_url = (
        f"{oidc_auth_endpoint()}"
        f"?client_id={os.getenv("AUTH_CLIENT_ID", "<NONE>")}"
        f"&response_type=code"
        f"&redirect_uri={os.getenv("AUTH_REDIRECT_URI", "<NONE>")}"
        f"&response_mode=query"
        f"&scope={AUTH_SCOPE}"
        f"&state={state}"
        f"&nonce={nonce}"
    )

    flask.abort(flask.redirect(auth_url))

@bp.get("/auth/callback")
def oauth_cb():
    if flask.request.args.get("state") != flask.session.get("state"):
        raise werkzeug.exceptions.BadRequest();

    if "error" in flask.request.args:
        raise werkzeug.exceptions.BadRequest();

    code = flask.request.args.get("code")

    token_response = requests.post(
        oidc_token_endpoint(),
        data={
            "client_id": os.getenv("AUTH_CLIENT_ID", "<NONE>"),
            "client_secret": os.getenv("AUTH_CLIENT_SECRET", "<NONE>"),
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": AUTH_REDIRECT_URI,
            "scope": AUTH_SCOPE,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        token_response.raise_for_status()
    except requests.HTTPError:
        raise werkzeug.exceptions.BadRequest();

    tokens = token_response.json()
    id_token = tokens.get('id_token')

    # Validate
    jwks = requests.get(oidc_jwks_endpoint()).json()["keys"]
    unverified_header = jwt.get_unverified_header(id_token)

    key = next(
        (k for k in jwks if k["kid"] == unverified_header["kid"]),
        None,
    )
    if key is None:
        raise Exception("Signing key not found")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

    try:
        claims = jwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience=os.getenv("AUTH_CLIENT_ID", "<NONE>"),
            issuer=oidc_issuer(),
        )

    except jwt.InvalidTokenError:
        raise werkzeug.exceptions.BadGateway()

    oidc_user = Account(id=claims["sub"], name=claims["name"], email=claims["email"])
    if not db.get_account_by_id(oidc_user.id):
        db.create_account(oidc_user)
    token = create_bearer_token(oidc_user.id)
    
    cb = flask.session.get("cb")
    if (not cb or (len(cb) > 0 and cb[0] == '/')):
        cb = ""

    response = flask.make_response(flask.redirect(f'/{cb}'))
    response.set_cookie('jwt_cookie', token)
    return response
