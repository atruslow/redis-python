




from asyncio import StreamReader, StreamWriter

from app import response
from app.parser import parser

import logging

logger = logger = logging.getLogger(__name__)


async def replication(reader: StreamReader, writer: StreamWriter) -> None:
    """
    Replicates data from a master without responding
    """
    
    logger.info("Awaiting data from master")

    while resp := await reader.read(1024):
    
        logger.info("Read data from master")

        command = resp.decode("utf-8")
        value = parser.parse_list(command)

        logger.info(f"Received {value}")

        response.parse_command(value)

        