import random
import sqlite3
import uuid
from flask import Flask, current_app, g
import click

import game
import typedefs

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
    data = [
        ("made short work of", "didn’t survive the night."),
        ("said “goodnight” to", "forgot how gravity works."),
        ("made early retirement plans for", "ignored a “wet floor” sign."),
        ("sent a strongly worded bullet to", "forgot to check their corners."),
        ("offered severance pay to", "proved that safety harnesses matter."),
        ("proved that hesitation kills — just ask", "overestimated their balance."),
        ("cleared the schedule of", "didn’t make it to the credits."),
        ("closed the case on", "fell for their own trap."),
        ("retired", "forgot to reload."),
        ("terminated", "cut the wrong wire."),
    ]
    db.executemany("""INSERT INTO log_messages (elim, forfeit) VALUES (?,?)""", data)
    db.commit()

@click.command('init-db')
def init_db_cmd():
    db = get_db()
    init_db(db)
    click.echo("Initialized the database")

    
def init_app(app: Flask):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_cmd)
    app.cli.add_command(game.create_game_cmd)
    app.cli.add_command(game.reset_game_cmd)

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
    u : list[typedefs.Game] = []
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

def set_game_owner(game_id: uuid.UUID, user_id: str, overwrite: bool = False) -> bool:
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

def create_account(account: typedefs.Account):
    db = get_db()
    try:
        db.execute("""INSERT INTO accounts (id, name, email) VALUES (?, ?, ?) """, 
                   (account.id, account.name, account.email))
        db.commit()
        return id
    except sqlite3.Error as e:
        print(e)
        db.rollback()
    return None

def get_account_by_id(user_id: str) -> typedefs.Account | None:
    db = get_db()
    try:
        cursor = db.execute("""
            SELECT * FROM accounts 
            WHERE id = ?""", 
                   (user_id,))
        row = cursor.fetchone()
        return typedefs.Account(
            id=row["id"], 
            name=row["name"],
            email=row["email"])
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

    return None

def create_user(game_id: uuid.UUID, account_id: str) -> bool:
    db = get_db()

    try:
        db.execute("""INSERT INTO USERS (account_id, game_id) VALUES (?, ?) """, 
                   (account_id, game_id.bytes))
        db.commit()
    except sqlite3.IntegrityError as _:
        db.rollback()
        return False
    except sqlite3.Error as _:
        db.rollback()
    return True 


def remove_user(game_id: uuid.UUID, user_id: str) -> bool:
    db = get_db()

    try:
        db.execute("""DELETE FROM users WHERE game_id = ? and account_id = ?""", 
                   (game_id.bytes, user_id))
        db.commit()
    except sqlite3.IntegrityError as e:
        print(e)
        db.rollback()
        return False
    except sqlite3.Error as e:
        print(e)
        db.rollback()
    return True 

def get_user_by_id(game_id: uuid.UUID, user_id: str) -> typedefs.User | None:
    db = get_db()

    try:
        cursor = db.execute("""
            SELECT users.*, accounts.* FROM users 
            LEFT JOIN accounts ON users.account_id = accounts.id
            WHERE account_id = ? AND game_id = ?""", 
                   (user_id, game_id.bytes))
        row = cursor.fetchone()
        return typedefs.User(
            id=row["id"], 
            name=row["name"],
            target_user_id=row["target_user_id"],
            eliminated=row["eliminated"],
            elimination_count=row["elimination_count"])
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

    return None

def get_user_by_target(game_id: uuid.UUID, target_id: str) -> typedefs.User | None:
    db = get_db()

    try:
        cursor = db.execute("""
            SELECT users.*, accounts.* FROM users 
            LEFT JOIN accounts ON users.account_id = accounts.id
            WHERE target_user_id = ? AND game_id = ?""", 
                   (target_id, game_id.bytes))
        row = cursor.fetchone()
        return typedefs.User(
            id=row["id"], 
            name=row["name"],
            target_user_id=row["target_user_id"],
            eliminated=row["eliminated"],
            elimination_count=row["elimination_count"])
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

    return None

def get_users_by_game(game_id: uuid.UUID) -> list[typedefs.User]:
    u : list[typedefs.User] = []
    db = get_db()

    try:
        cursor = db.execute("""
            SELECT users.*, accounts.* FROM users 
            LEFT JOIN accounts ON users.account_id = accounts.id
            WHERE game_id = ?
            ORDER BY eliminated ASC, elimination_count DESC, name ASC""", 
                   (game_id.bytes,))
        for row in cursor.fetchall():
            u.append(typedefs.User(
                id=row["id"], 
                name=row["name"],
                target_user_id=row["target_user_id"],
                eliminated=row["eliminated"],
                elimination_count=row["elimination_count"]))
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

    return u 

def set_user_targets(game_id: uuid.UUID, mapping: list[tuple[str, str]]):
    db = get_db()
    data = [(e[1], game_id.bytes, e[0]) for e in mapping]

    try:
        db.executemany("""
            UPDATE users
            SET target_user_id = ?
            WHERE game_id = ? AND account_id = ?""", 
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

def eliminate_user(game_id: uuid.UUID, target_id: str, elim_count: int):
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
            WHERE game_id = ? AND account_id = ?""", 
                   (game_id.bytes, target.id))
        db.execute("""
            UPDATE users 
            SET target_user_id = ?, elimination_count = elimination_count + ?
            WHERE game_id = ? AND account_id = ?
        """, (target.target_user_id, elim_count, game_id.bytes, assassin.id))
        cursor = db.execute("""SELECT COUNT(*) FROM log_messages""")
        row_count = cursor.fetchone()[0]
        msg_id = random.randint(1, row_count)
        db.execute("""
            INSERT INTO logs (game_id, user_id, target_id, msg_id) VALUES (?, ?, ?, ?)
        """, (game_id.bytes, assassin.id if elim_count else None, target_id, msg_id))
        db.commit()
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

def get_game_logs(game_id: uuid.UUID) -> list[typedefs.Log]:
    l : list[typedefs.Log] = []
    db = get_db()

    try:
        cursor = db.execute("""
            SELECT accounts.name AS user, targets.name AS target, log_messages.* FROM logs
            LEFT JOIN accounts ON accounts.id = logs.user_id
            LEFT JOIN accounts AS targets ON targets.id = logs.target_id
            LEFT JOIN log_messages ON logs.msg_id = log_messages.id
            WHERE logs.game_id = ?
            ORDER BY logs.ts ASC""", 
                   (game_id.bytes,))
        for row in cursor.fetchall():
            l.append(typedefs.Log(
                user=row["user"], 
                target=row["target"],
                elim_msg=row["elim"],
                forfeit_msg=row["forfeit"]))
    except sqlite3.Error as e:
        print(e)
    except Exception as e:
        print(e)

    return l

def reset_game(game_id: uuid.UUID):
    db = get_db()

    try:
        db.execute("""
        DELETE FROM logs
        WHERE logs.game_id = ?
        """,
           (game_id.bytes,))
        db.execute("""
            UPDATE users SET
            target_user_id = NULL,
            eliminated = 0,
            elimination_count = '0'
            WHERE game_id = ?
        """,
            (game_id.bytes,))
        db.execute("""
            UPDATE games SET
            started = 0
            WHERE uuid = ?
        """,
           (game_id.bytes,))
        db.commit()
    except sqlite3.Error as e:
        print(f"db::reset_game: {e}")

