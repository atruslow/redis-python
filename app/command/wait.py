import asyncio
import time
from typing import List

from app.command.const import Command, ParsedCommand
from app.replica import replication


def handle_wait(args: List[str]) -> ParsedCommand:

    num_replicas, timeout = args

    replica_count = replication.num_replicas()


    #time.sleep(int(timeout))

    return ParsedCommand(command=Command.Wait, args=args, response=replica_count)
