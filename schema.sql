DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS games;

CREATE TABLE games (
  uuid BLOB(16) PRIMARY KEY,
  name TEXT NOT NULL,
  owner_id INTEGER,
  started INTEGER NOT NULL DEFAULT 0,

  FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE SET NULL,
  FOREIGN KEY(uuid, owner_id) REFERENCES users(game_id, id)
);

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  game_id BLOB(16) NOT NULL,
  username TEXT NOT NULL,
  password TEXT NOT NULL,

  target_user_id INTEGER, 
  eliminated INTEGER NOT NULL DEFAULT 0,
  elimination_count INTEGER NOT NULL DEFAULT 0, 

  FOREIGN KEY(game_id) REFERENCES games(uuid) ON DELETE CASCADE,
  FOREIGN KEY(game_id, target_user_id) REFERENCES users(game_id, target_user_id),
  UNIQUE (game_id, target_user_id),
  UNIQUE (game_id, username),
  UNIQUE (game_id, id)
);

