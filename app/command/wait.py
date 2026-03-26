import asyncio
from typing import List

from app.command.const import Command, ParsedCommand
from app.replica import replication


async def handle_wait(args: List[str]) -> ParsedCommand:
    num_replicas, timeout = args

    replica_count = replication.num_replicas()

    if replica_count == 0:
        return ParsedCommand(command=Command.Wait, args=args, response=replica_count)

    await asyncio.sleep(int(timeout) / 1000)

    return ParsedCommand(command=Command.Wait, args=args, response=replica_count)
