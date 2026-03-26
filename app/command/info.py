from dataclasses import asdict, dataclass
from enum import StrEnum, auto
from typing import List, Optional

from app.command.const import Command, ParsedCommand

REPLICATION_INFO: Optional["ReplicationInfo"] = None


class ReplicationRole(StrEnum):
    MASTER = auto()
    SLAVE = auto()


@dataclass
class ReplicationInfo:
    role: ReplicationRole = ReplicationRole.MASTER
    connected_slaves: int = 0
    master_replid: str = "8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb"
    master_repl_offset: int = 0

    def as_dict(self):
        return asdict(self)

    def __str__(self) -> str:
        return "\r\n".join(
            [
                f"{k}:{v}"
                for k, v in self.as_dict().items()
                if k in ["role", "master_replid", "master_repl_offset"]
            ]
        )

    @property
    def is_slave(self):
        return self.role is ReplicationRole.SLAVE

    def increment_offset(self, count: int) -> None:
        self.master_repl_offset += count


def handle_info(args: List[str]) -> ParsedCommand:
    """
    Returns the info requested from an INFO command
    """
    return ParsedCommand(
        command=Command.Info, args=args, response=str(get_info()).encode()
    )


def init_info(**kwargs) -> ReplicationInfo:
    global REPLICATION_INFO
    REPLICATION_INFO = ReplicationInfo(**kwargs)
    return REPLICATION_INFO


def get_info() -> ReplicationInfo:
    if REPLICATION_INFO is None:
        raise RuntimeError("ReplicationInfo has not been initialized")
    return REPLICATION_INFO
