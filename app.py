import flask
import db
import game

def create_app() -> flask.Flask:
    app = flask.Flask(__name__)
    app.secret_key = "secret_key"

    # Register db shutdown funcs
    db.init_app(app)
    
    # Register Blueprints
    app.register_blueprint(game.bp)

    @app.errorhandler(400)
    def _(_):
        return "Bad Request", 400

    @app.errorhandler(404)
    def _(_):
        return flask.render_template('not-found.html'), 404


    return app


