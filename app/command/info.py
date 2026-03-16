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
    master_replid: int = 0
    master_repl_offset: int = 0

    def as_dict(self):
        return asdict(self)
    
    def __str__(self) -> str:

        formatted_dict = "".join([f"{k}:{v}" for k,v in self.as_dict().items() if k == "role"])

        return formatted_dict


def handle_info(args: List[str]) -> ParsedCommand:
    """
    Returns the info requested from an INFO command
    """

    info = set_or_get_info()

    return ParsedCommand(command=Command.Info, args=args, response=str(info))

def set_or_get_info(**kwargs) -> ReplicationInfo:

    global REPLICATION_INFO

    if not REPLICATION_INFO:
        REPLICATION_INFO = ReplicationInfo(**kwargs)
    
    return REPLICATION_INFO