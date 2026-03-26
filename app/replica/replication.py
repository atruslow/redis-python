




from asyncio import StreamReader, StreamWriter

from app import response
from app.parser import parser


async def replication(reader: StreamReader, writer: StreamWriter) -> None:
    """
    Replicates data from a master without responding
    """
    
    while resp := await reader.read(1024):

        command = resp.decode("utf-8")
        value = parser.parse_list(command)
        response.parse_command(value)

        