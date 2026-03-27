import asyncio
from typing import List

from app.command.const import Command, ParsedCommand
from app.replica import replication


async def handle_wait(args: List[str]) -> ParsedCommand:
    num_replicas, timeout = args

    replica_count = await replication.num_replicas(int(num_replicas), int(timeout))

    return ParsedCommand(command=Command.Wait, args=args, response=replica_count)
