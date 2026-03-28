import argparse
import asyncio
import logging
import re
import sys

from app.server.server import run_server

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_PORT = 6379
HOST_PORT_RE = re.compile(r"^(?P<host>\S+)\s+(?P<port>\d+)$")


def main():
    """
    Main entrypoint for the server
    """
    parser = argparse.ArgumentParser(
        prog="Redis in Python", description="Toy Redis Implementation in Python"
    )

    parser.add_argument("-p", "--port", default=REDIS_PORT)
    parser.add_argument("--replicaof", type=_parse_host_port)

    asyncio.run(run_server(parser.parse_args()))


def _parse_host_port(arg_value: str) -> tuple[str, str]:
    if m := HOST_PORT_RE.match(arg_value):
        return m.group("host"), m.group("port")
    raise argparse.ArgumentTypeError(
        f"'{arg_value}' is an invalid value. Does not match pattern: {HOST_PORT_RE}"
    )


if __name__ == "__main__":
    main()
