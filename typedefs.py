import uuid
from dataclasses import dataclass

class Game:
    def __init__(self, id: uuid.UUID, name: str, owner: str | None, started: bool, announcement: str | None) -> None:
        self.id = id
        self.name = name
        self.owner = owner
        self.started = started
        self.announcement = announcement

@dataclass
class Account:
    id: str
    name: str
    email: str

@dataclass
class User:
    id: str
    name: str
    target_user_id: str | None
    eliminated: bool
    elimination_count: int

@dataclass
class Log:
    user: str
    target: str
    elim_msg: str
    forfeit_msg: str

    def to_str(self) -> str:
        if self.user:
            return f"{self.user} {self.elim_msg} {self.target}"
        else:
            return f"{self.target} {self.forfeit_msg}"

