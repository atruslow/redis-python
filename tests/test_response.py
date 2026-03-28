import pytest

from app.command import response
from app.command.const import Command, ParsedCommand


@pytest.mark.asyncio
async def test_parse_command_ping():
    assert await response.parse_command(["ping"]) == ParsedCommand(
        command=Command.Ping, args=[], response="PONG"
    )


@pytest.mark.asyncio
async def test_parse_command_echo():
    assert await response.parse_command(["echo", "hey"]) == ParsedCommand(
        command=Command.Echo, args=["hey"], response=b"hey"
    )


@pytest.mark.asyncio
async def test_parse_command_echo_multiple_words():
    assert await response.parse_command(["echo", "hello", "world"]) == ParsedCommand(
        command=Command.Echo, args=["hello", "world"], response=b"hello world"
    )


@pytest.mark.asyncio
async def test_parse_command_set():
    assert await response.parse_command(["set", "foo", "bar"]) == ParsedCommand(
        command=Command.Set, args=["foo", "bar"], response="OK"
    )


@pytest.mark.asyncio
async def test_parse_command_get_missing_key():
    result = await response.parse_command(["get", "no_such_key_99"])
    assert result.command == Command.Get
    assert result.response is None


@pytest.mark.asyncio
async def test_parse_command_get_existing_key():
    await response.parse_command(["set", "baz", "qux"])
    result = await response.parse_command(["get", "baz"])
    assert result.command == Command.Get
    assert result.response == b"qux"


@pytest.mark.asyncio
async def test_parse_command_replconf():
    assert await response.parse_command(
        ["REPLCONF", "listening-port", "6380"]
    ) == ParsedCommand(
        command=Command.Replconf, args=["listening-port", "6380"], response="OK"
    )


@pytest.mark.asyncio
async def test_parse_command_replconf_capa_psync2():
    assert await response.parse_command(
        ["REPLCONF", "capa", "psync2"]
    ) == ParsedCommand(command=Command.Replconf, args=["capa", "psync2"], response="OK")


@pytest.mark.asyncio
async def test_parse_command_unknown_raises():
    with pytest.raises(RuntimeError):
        await response.parse_command(["unknown"])


@pytest.mark.asyncio
async def test_parse_command_info():
    result = await response.parse_command(["INFO", "replication"])
    assert result.command == Command.Info
    assert b"role" in result.response


@pytest.mark.asyncio
async def test_parse_command_psync():
    result = await response.parse_command(["PSYNC", "?", "-1"])
    assert result.command == Command.Psync
    assert "FULLRESYNC" in result.response


@pytest.mark.asyncio
async def test_parse_command_wait():
    from app.replica import replication

    replication.REPLICA_STREAMS.clear()
    result = await response.parse_command(["WAIT", "1", "500"])
    assert result.command == Command.Wait
    assert result.response == 0
