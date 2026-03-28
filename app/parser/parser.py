"""
RESP (Redis Serialization Protocol) parser and encoder.

Supports the full RESP2 type set:
  + Simple String   "+OK\r\n"
  - Error           "-ERR message\r\n"
  : Integer         ":42\r\n"
  $ Bulk String     "$5\r\nhello\r\n"  /  $-1\r\n  (null)
  * Array           "*2\r\n..."         /  *-1\r\n  (null)
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Union


class RESPType(Enum):
    """RESP type prefix characters."""

    SIMPLE_STRING = "+"
    ERROR = "-"
    INTEGER = ":"
    BULK_STRING = "$"
    ARRAY = "*"


# A RESP value is one of these Python types (None represents a null bulk/array).
RESPValue = Union[str, "RESPError", int, bytes, Sequence["RESPValue"], None]


@dataclass
class RESPError:
    """Represents a RESP error (-prefix)."""

    message: str

    def __str__(self) -> str:
        return self.message


class RESPParseError(ValueError):
    """Raised when the input does not conform to the RESP protocol."""


def parse_list(data: str) -> list[str]:
    """Parse a RESP-encoded string and return its contents as a plain list of strings."""
    value = parse_str(data)

    if not isinstance(value, list) or not all(isinstance(i, str) for i in value):
        raise ValueError("Incorrect Data")

    return [str(i) for i in value]


def parse_str(data: str) -> RESPValue:
    """Convenience wrapper around ``parse`` that accepts a string instead of bytes."""
    value, _ = parse(data.encode())
    return value


def parse(data: bytes) -> tuple[RESPValue, int]:
    """
    Parse one RESP value from *data* and return ``(value, bytes_consumed)``.

    *value* is:
      - ``str``       for Simple Strings
      - ``RESPError`` for Errors
      - ``int``       for Integers
      - ``bytes``     for Bulk Strings  (``None`` for null bulk string)
      - ``list``      for Arrays        (``None`` for null array)

    Raises ``RESPParseError`` on malformed input.
    """
    if not data:
        raise RESPParseError("Empty input")

    prefix = chr(data[0])
    try:
        resp_type = RESPType(prefix)
    except ValueError as e:
        raise RESPParseError(f"Unknown RESP type prefix: {prefix!r}") from e

    match resp_type:
        case RESPType.SIMPLE_STRING:
            return _parse_simple_string(data)
        case RESPType.ERROR:
            return _parse_error(data)
        case RESPType.INTEGER:
            return _parse_integer(data)
        case RESPType.BULK_STRING:
            return _parse_bulk_string(data)
        case RESPType.ARRAY:
            return _parse_array(data)


def parse_all(data: bytes) -> list[RESPValue]:
    """Parse all RESP values contained in *data* and return them as a list."""
    values: list[RESPValue] = []
    offset = 0
    while offset < len(data):
        value, consumed = parse(data[offset:])
        values.append(value)
        offset += consumed
    return values


async def parse_stream(reader: asyncio.StreamReader) -> list[str] | None:
    """
    Read one complete RESP array command from *reader*.
    Returns a list of string args, or None on EOF.
    """
    header = await reader.readline()
    if not header:
        return None
    count = int(header[1:].strip())

    args = []
    for _ in range(count):
        length_line = await reader.readline()
        length = int(length_line[1:].strip())
        payload = await reader.readexactly(length + 2)  # +2 for \r\n
        args.append(payload[:-2].decode())

    return args


def _read_line(data: bytes) -> tuple[bytes, int]:
    idx = data.find(b"\r\n")
    if idx == -1:
        raise RESPParseError("Missing CRLF terminator")
    return data[1:idx], idx + 2  # skip the type prefix byte


def _parse_simple_string(data: bytes) -> tuple[str, int]:
    line, consumed = _read_line(data)
    return line.decode(), consumed


def _parse_error(data: bytes) -> tuple[RESPError, int]:
    line, consumed = _read_line(data)
    return RESPError(line.decode()), consumed


def _parse_integer(data: bytes) -> tuple[int, int]:
    line, consumed = _read_line(data)
    try:
        return int(line), consumed
    except ValueError as e:
        raise RESPParseError(f"Invalid integer: {line!r}") from e


def _parse_bulk_string(data: bytes) -> tuple[bytes | None, int]:
    length_line, header_consumed = _read_line(data)
    try:
        length = int(length_line)
    except ValueError as e:
        raise RESPParseError(f"Invalid bulk string length: {length_line!r}") from e

    if length == -1:
        return None, header_consumed

    total_needed = header_consumed + length + 2  # +2 for trailing \r\n
    if len(data) < total_needed:
        raise RESPParseError("Incomplete bulk string data")

    payload = data[header_consumed : header_consumed + length]
    return payload, total_needed


def _parse_array(data: bytes) -> tuple[list[RESPValue] | None, int]:
    count_line, header_consumed = _read_line(data)
    try:
        count = int(count_line)
    except ValueError as e:
        raise RESPParseError(f"Invalid array count: {count_line!r}") from e

    if count == -1:
        return None, header_consumed

    elements: list[RESPValue] = []
    offset = header_consumed
    for _ in range(count):
        value, consumed = parse(data[offset:])
        elements.append(value)
        offset += consumed

    return elements, offset


def encode(value: RESPValue) -> bytes:
    """
    Encode a Python value into its RESP wire representation.

    Accepted types:
      - ``str``       → Simple String  (``+…\r\n``)
      - ``RESPError`` → Error          (``-…\r\n``)
      - ``int``       → Integer        (``:…\r\n``)
      - ``bytes``     → Bulk String    (``$…\r\n…\r\n``)
      - ``None``      → Null Bulk String (``$-1\r\n``)
      - ``list``      → Array          (``*…\r\n…``)
    """
    match value:
        case str():
            return _encode_simple_string(value)
        case RESPError():
            return _encode_error(value)
        case int():
            return _encode_integer(value)
        case bytes():
            return _encode_bulk_string(value)
        case None:
            return b"$-1\r\n"
        case list():
            return _encode_array(value)
        case _:
            raise TypeError(f"Cannot encode type {type(value).__name__!r} as RESP")


def encode_bulk_string(value: str) -> bytes:
    """Convenience wrapper: encode a str as a RESP Bulk String (not Simple String)."""
    return _encode_bulk_string(value.encode())


def encode_list(msg: list[str]) -> bytes:
    """Encode a list of strings as a RESP array of bulk strings."""
    return encode([a.encode() for a in msg])


def _encode_simple_string(value: str) -> bytes:
    if "\r" in value or "\n" in value:
        raise ValueError("Simple strings must not contain CR or LF")
    return f"+{value}\r\n".encode()


def _encode_error(value: RESPError) -> bytes:
    return f"-{value.message}\r\n".encode()


def _encode_integer(value: int) -> bytes:
    return f":{value}\r\n".encode()


def _encode_bulk_string(value: bytes) -> bytes:
    return b"$" + str(len(value)).encode() + b"\r\n" + value + b"\r\n"


def _encode_array(value: list[RESPValue]) -> bytes:
    header = f"*{len(value)}\r\n".encode()
    return header + b"".join(encode(item) for item in value)
