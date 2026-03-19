DROP TABLE IF EXISTS logs;
DROP TABLE IF EXISTS log_messages;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS games;

CREATE TABLE games (
  uuid BLOB(16) PRIMARY KEY,
  name TEXT NOT NULL,
  owner_id TEXT,
  started INTEGER NOT NULL DEFAULT 0,
  announcement TEXT,

  FOREIGN KEY(owner_id) REFERENCES users(account_id) ON DELETE SET NULL,
  FOREIGN KEY(uuid, owner_id) REFERENCES users(game_id, account_id)
);

CREATE TABLE accounts (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL
);

CREATE TABLE users (
  account_id TEXT PRIMARY KEY,
  game_id BLOB(16) NOT NULL,

  target_user_id INTEGER, 
  eliminated INTEGER NOT NULL DEFAULT 0,
  elimination_count INTEGER NOT NULL DEFAULT 0, 

  UNIQUE (game_id, account_id),
  UNIQUE (game_id, target_user_id),
  FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE,
  FOREIGN KEY(game_id) REFERENCES games(uuid) ON DELETE CASCADE
  -- FOREIGN KEY(game_id, target_user_id) REFERENCES users(game_id, account_id)
);

CREATE TABLE log_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  elim TEXT NOT NULL,
  forfeit TEXT NOT NULL
);

CREATE TABLE logs (
  game_id BLOB(16) NOT NULL,
  user_id TEXT,
  target_id TEXT NOT NULL,
  msg_id INTEGER NOT NULL,
  ts TEXT NOT NULL DEFAULT (datetime('now')),

  PRIMARY KEY(game_id, target_id),
  FOREIGN KEY(game_id) REFERENCES games(uuid) ON DELETE CASCADE,
  FOREIGN KEY(user_id) REFERENCES users(account_id) ON DELETE CASCADE,
  FOREIGN KEY(target_id) REFERENCES users(account_id) ON DELETE CASCADE,
  FOREIGN KEY(msg_id) REFERENCES log_messages(id)
);


