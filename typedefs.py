import uuid


class Game:
    def __init__(self, id: uuid.UUID, name: str, owner: int | None, started: bool, announcement: str | None) -> None:
        self.id = id
        self.name = name
        self.owner = owner
        self.started = started
        self.announcement = announcement

class User:
    def __init__(self, id: int, username: str, password_hash: bytes, target_user_id: int | None, eliminated: bool, elimination_count: int) -> None:
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.target_user_id = target_user_id
        self.eliminated = eliminated
        self.elimination_count = elimination_count
