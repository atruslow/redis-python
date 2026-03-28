from dataclasses import asdict, dataclass
from enum import StrEnum, auto
from typing import Optional

from app.command.const import Command, ParsedCommand

REPLICATION_INFO: Optional["ReplicationInfo"] = None


class ReplicationRole(StrEnum):
    """Replication role for this server instance."""

    MASTER = auto()
    SLAVE = auto()


@dataclass
class ReplicationInfo:
    """Holds replication state shared across the server (role, offset, replication ID)."""

    role: ReplicationRole = ReplicationRole.MASTER
    connected_slaves: int = 0
    master_replid: str = "8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb"
    master_repl_offset: int = 0

    def as_dict(self):
        """Return all fields as a plain dict."""
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
        """True if this instance is running as a replica."""
        return self.role is ReplicationRole.SLAVE

    def increment_offset(self, count: int) -> None:
        """Advance the replication offset by count bytes."""
        self.master_repl_offset += count


async def handle_info(args: list[str]) -> ParsedCommand:
    """
    Returns the info requested from an INFO command
    """
    return ParsedCommand(
        command=Command.Info, args=args, response=str(get_info()).encode()
    )


def init_info(**kwargs) -> ReplicationInfo:
    """Create and store the global ReplicationInfo; call once at startup."""
    global REPLICATION_INFO
    REPLICATION_INFO = ReplicationInfo(**kwargs)
    return REPLICATION_INFO


def get_info() -> ReplicationInfo:
    """Return the global ReplicationInfo; raises RuntimeError if not yet initialized."""
    if REPLICATION_INFO is None:
        raise RuntimeError("ReplicationInfo has not been initialized")
    return REPLICATION_INFO
