from os import stat_result
import sqlite3
import uuid
from flask import Flask, current_app, g
import click

import game
import typedefs

connection = sqlite3.connect('db.sqlite')

def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect('./data/db.sqlite')
        g.db.execute("PRAGMA foreign_keys = ON;")
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(_=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db(db: sqlite3.Connection) -> None:
    with current_app.open_resource('schema.sql') as schema:
        db.executescript(schema.read().decode('utf8'))

@click.command('init-db')
def init_db_cmd():
    db = get_db()
    init_db(db)
    click.echo("Initialized the database")
    
def init_app(app: Flask):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_cmd)
    app.cli.add_command(game.create_game_cmd)

def create_game(name: str) -> uuid.UUID | None:
    db = get_db()
    try:
        id = uuid.uuid4()
        db.execute("""INSERT INTO games (uuid, name) VALUES (?, ?) """, 
                   (id.bytes, name))
        db.commit()
        return id
    except sqlite3.Error as e:
        print(e)
        db.rollback()
    return None

def get_games() -> list[typedefs.Game]:
    u = []
    db = get_db()

    try:
        cursor = db.execute("""
            SELECT * FROM games 
            ORDER BY name""")
        for row in cursor.fetchall():
            u.append(typedefs.Game(
                id=uuid.UUID(bytes=row["uuid"]), 
                name=row["name"], 
                owner=row["owner_id"], 
                started=row["started"],
                announcement=row["announcement"]))
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

    return u 

def get_game_by_id(id: uuid.UUID) -> typedefs.Game | None:
    db = get_db()

    try:
        cursor = db.execute("""SELECT * FROM games WHERE uuid = ?""", 
                   (id.bytes,))
        row = cursor.fetchone()
        return typedefs.Game(
            id=uuid.UUID(bytes=row["uuid"]),
            name=row["name"],
            owner=row["owner_id"], 
            started=row["started"],
            announcement=row["announcement"]) 
    except Exception as e:
        print(e)
    return None

def set_game_owner(game_id: uuid.UUID, user_id: int, overwrite: bool = False) -> bool:
    db = get_db()
    try:
        db.execute("""UPDATE games SET owner_id = ?
                    WHERE uuid = ? AND (? OR owner_id IS NULL)""", 
                   (user_id, game_id.bytes, overwrite))
        db.commit()
    except sqlite3.Error as e:
        print(e)
        db.rollback()
    return True 

def set_game_announcement(game_id: uuid.UUID, msg: str | None) -> bool:
    db = get_db()
    try:
        db.execute("""UPDATE games SET announcement = ?
                    WHERE uuid = ?""", 
                   (msg, game_id.bytes))
        db.commit()
    except sqlite3.Error as e:
        print(e)
        db.rollback()
    return True 


def create_user(game_id: uuid.UUID, username: str, password_hash: bytes) -> bool:
    db = get_db()

    try:
        db.execute("""INSERT INTO USERS (username, password, game_id) VALUES (?, ?, ?) """, 
                   (username, password_hash, game_id.bytes))
        db.commit()
    except sqlite3.IntegrityError as _:
        db.rollback()
        return False
    except sqlite3.Error as _:
        db.rollback()
    return True 

def remove_user(game_id: uuid.UUID, user_id: int) -> bool:
    db = get_db()

    try:
        db.execute("""DELETE FROM users WHERE game_id = ? and id = ?""", 
                   (game_id.bytes, user_id))
        db.commit()
    except sqlite3.IntegrityError as _:
        db.rollback()
        return False
    except sqlite3.Error as _:
        db.rollback()
    return True 

def get_user_by_username(game_id: uuid.UUID, username: str) -> typedefs.User | None:
    db = get_db()

    try:
        cursor = db.execute("""
            SELECT * FROM users 
            WHERE username = ? AND game_id = ?""", 
                   (username, game_id.bytes))
        row = cursor.fetchone()
        return typedefs.User(
            id=row["id"], 
            username=row["username"],
            password_hash=row["password"], 
            target_user_id=row["target_user_id"],
            eliminated=row["eliminated"],
            elimination_count=row["elimination_count"])
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

    return None

def get_user_by_id(game_id: uuid.UUID, user_id: int) -> typedefs.User | None:
    db = get_db()

    try:
        cursor = db.execute("""
            SELECT * FROM users 
            WHERE id = ? AND game_id = ?""", 
                   (user_id, game_id.bytes))
        row = cursor.fetchone()
        return typedefs.User(
            id=row["id"], 
            username=row["username"],
            password_hash=row["password"], 
            target_user_id=row["target_user_id"],
            eliminated=row["eliminated"],
            elimination_count=row["elimination_count"])
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

    return None

def get_user_by_target(game_id: uuid.UUID, target_id: int) -> typedefs.User | None:
    db = get_db()

    try:
        cursor = db.execute("""
            SELECT * FROM users 
            WHERE target_user_id = ? AND game_id = ?""", 
                   (target_id, game_id.bytes))
        row = cursor.fetchone()
        return typedefs.User(
            id=row["id"], 
            username=row["username"],
            password_hash=row["password"], 
            target_user_id=row["target_user_id"],
            eliminated=row["eliminated"],
            elimination_count=row["elimination_count"])
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

    return None

def get_users_by_game(game_id: uuid.UUID) -> list[typedefs.User]:
    u = []
    db = get_db()

    try:
        cursor = db.execute("""
            SELECT * FROM users 
            WHERE game_id = ?
            ORDER BY eliminated ASC, elimination_count DESC, username ASC""", 
                   (game_id.bytes,))
        for row in cursor.fetchall():
            u.append(typedefs.User(
                id=row["id"], 
                username=row["username"],
                password_hash=row["password"], 
                target_user_id=row["target_user_id"],
                eliminated=row["eliminated"],
                elimination_count=row["elimination_count"]))
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

    return u 

def set_user_targets(game_id: uuid.UUID, mapping: list[tuple[int, int]]):
    db = get_db()
    data = [(e[1], game_id.bytes, e[0]) for e in mapping]

    try:
        db.executemany("""
            UPDATE users
            SET target_user_id = ?
            WHERE game_id = ? AND id = ?""", 
                   data)
        db.execute("""
            UPDATE games
            SET started = 1
            WHERE uuid = ?
        """, (game_id.bytes,))
        db.commit()
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

def eliminate_user(game_id: uuid.UUID, target_id: int, elim_count: int):
    target = get_user_by_id(game_id, target_id)
    if not target or not target.target_user_id:
        return

    assassin = get_user_by_target(game_id, target_id)
    if not assassin: 
        return

    db = get_db()
    try:
        db.execute("""
            UPDATE users
            SET eliminated = 1, target_user_id = NULL
            WHERE game_id = ? AND id = ?""", 
                   (game_id.bytes, target.id))
        db.execute("""
            UPDATE users 
            SET target_user_id = ?, elimination_count = elimination_count + ?
            WHERE game_id = ? AND id = ?
        """, (target.target_user_id, elim_count, game_id.bytes, assassin.id))
        db.commit()
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)


