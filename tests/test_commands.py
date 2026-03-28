import pytest

from app.cache.cache import CACHE
from app.command import get as get_cmd
from app.command import info as info_cmd
from app.command import psync as psync_cmd
from app.command import replconf
from app.command import set as set_cmd
from app.command import wait as wait_cmd
from app.command.const import Command, ParsedCommand
from app.command.info import ReplicationInfo, ReplicationRole
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


def test_replication_info_str():
    info = ReplicationInfo()
    result = str(info)
    assert "role:master" in result
    assert "master_repl_offset:0" in result


def test_replication_info_as_dict():
    info = ReplicationInfo()
    d = info.as_dict()
    assert d["role"] == "master"
    assert d["master_repl_offset"] == 0


def test_replication_info_increment_offset(initialize_info):
    from app.command.info import get_info

    get_info().increment_offset(31)
    assert get_info().master_repl_offset == 31


@pytest.mark.asyncio
async def test_handle_info(initialize_info):
    result = await info_cmd.handle_info(["replication"])
    assert result.command == Command.Info
    assert b"role:master" in result.response


def test_get_info_raises_when_not_initialized():
    import app.command.info as info_module

    original = info_module.REPLICATION_INFO
    info_module.REPLICATION_INFO = None
    try:
        with pytest.raises(RuntimeError, match="not been initialized"):
            info_module.get_info()
    finally:
        info_module.REPLICATION_INFO = original


@pytest.mark.asyncio
async def test_handle_psync(initialize_info):
    result = await psync_cmd.handle_psync(["?", "-1"])
    assert result.command == Command.Psync
    assert "FULLRESYNC" in result.response
    assert result.raw_extra is not None
    assert result.raw_extra.startswith(b"$")


@pytest.mark.asyncio
async def test_handle_wait_no_replicas(initialize_info):
    from app.replica import replication

    replication.REPLICA_STREAMS.clear()
    result = await wait_cmd.handle_wait(["1", "500"])
    assert result.command == Command.Wait
    assert result.response == 0
