import pytest
from app.cache.cache import CACHE
from app.command import set as set_cmd, get as get_cmd
from app.command.const import Command, ParsedCommand
from app.command.info import ReplicationRole, get_info
from app.command import replconf, info as info_cmd
from app.parser import parser as resp_parser


@pytest.fixture(autouse=True)
def clear_cache():
    CACHE.clear()


# ---------------------------------------------------------------------------
# SET
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_set_basic():
    result = await set_cmd.handle_set(["foo", "bar"])
    assert result == ParsedCommand(
        command=Command.Set, args=["foo", "bar"], response="OK"
    )


@pytest.mark.asyncio
async def test_handle_set_px():
    result = await set_cmd.handle_set(["foo", "bar", "px", "5000"])
    assert result.response == "OK"
    assert CACHE["foo"].expiry is not None


@pytest.mark.asyncio
async def test_handle_set_ex():
    result = await set_cmd.handle_set(["foo", "bar", "ex", "5"])
    assert result.response == "OK"
    assert CACHE["foo"].expiry is not None


def test_parse_expiry_px():
    result = set_cmd._parse_expiry(["px", "200"])
    assert result == 200


def test_parse_expiry_ex():
    result = set_cmd._parse_expiry(["ex", "2"])
    assert result == 2000


def test_parse_expiry_none():
    assert set_cmd._parse_expiry([]) is None


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_get_existing():
    await set_cmd.handle_set(["foo", "bar"])
    result = await get_cmd.handle_get(["foo"])
    assert result.response == b"bar"


@pytest.mark.asyncio
async def test_handle_get_missing():
    result = await get_cmd.handle_get(["missing"])
    assert result.response is None


# ---------------------------------------------------------------------------
# REPLCONF
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replconf_listening_port():
    result = await replconf.handle_replconf(["listening-port", "6380"])
    assert result.response == "OK"
    assert not result.replication_response


@pytest.mark.asyncio
async def test_replconf_getack_as_slave(initialize_info):
    from app.command.info import init_info

    init_info(role=ReplicationRole.SLAVE)
    result = await replconf.handle_replconf(["GETACK", "*"])
    assert result.replication_response
    assert result.response == [b"REPLCONF", b"ACK", b"0"]


@pytest.mark.asyncio
async def test_replconf_getack_as_master():
    result = await replconf.handle_replconf(["GETACK", "*"])
    assert result.response == "OK"
    assert not result.replication_response


# ---------------------------------------------------------------------------
# original_command encoding
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_original_command_set():
    cmd = await set_cmd.handle_set(["foo", "bar"])
    assert cmd.original_command == b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"


@pytest.mark.asyncio
async def test_original_command_set_with_px():
    cmd = await set_cmd.handle_set(["foo", "bar", "px", "1000"])
    assert (
        cmd.original_command
        == b"*5\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n$2\r\npx\r\n$4\r\n1000\r\n"
    )


# ---------------------------------------------------------------------------
# parse_stream
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parse_stream_basic():
    import asyncio

    reader = asyncio.StreamReader()
    reader.feed_data(b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")
    result = await resp_parser.parse_stream(reader)
    assert result == ["SET", "foo", "bar"]


@pytest.mark.asyncio
async def test_parse_stream_eof():
    import asyncio

    reader = asyncio.StreamReader()
    reader.feed_eof()
    result = await resp_parser.parse_stream(reader)
    assert result is None


@pytest.mark.asyncio
async def test_parse_stream_multiple_commands():
    import asyncio

    reader = asyncio.StreamReader()
    reader.feed_data(
        b"*3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n*2\r\n$3\r\nGET\r\n$3\r\nfoo\r\n"
    )
    first = await resp_parser.parse_stream(reader)
    second = await resp_parser.parse_stream(reader)
    assert first == ["SET", "foo", "bar"]
    assert second == ["GET", "foo"]
