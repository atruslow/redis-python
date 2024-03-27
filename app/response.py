import asyncio
from typing import List


async def async_parse(msg: str) -> List[str]:
    return await asyncio.get_event_loop().run_in_executor(None, parse, msg)


def parse(msg: str) -> List[str]:
    """
    Parses a decoded message from Redis, and returns a list of items
    """
    parsed_list = msg.split("\r\n")

    parsed_list = [
        i for i in parsed_list if i and not (i.startswith("*") or i.startswith("$"))
    ]

    return parsed_list
