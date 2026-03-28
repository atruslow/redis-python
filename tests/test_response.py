import pytest

from app import response
from app.command.const import Command, ParsedCommand
from app.parser.parser import RESPParseError


@pytest.mark.asyncio
async def test_response_parses():
    assert await response.parse("*1\r\n$4\r\nping\r\n") == ParsedCommand(
        command=Command.Ping, args=[], response="PONG"
    )


@pytest.mark.asyncio
async def test_respose_parses_echo():
    assert await response.parse("*2\r\n$4\r\necho\r\n$3\r\nhey\r\n") == ParsedCommand(
        command=Command.Echo, args=["hey"], response=b"hey"
    )


@pytest.mark.asyncio
async def test_response_parses_echo_multiple_words():
    assert await response.parse(
        "*3\r\n$4\r\necho\r\n$5\r\nhello\r\n$5\r\nworld\r\n"
    ) == ParsedCommand(
        command=Command.Echo, args=["hello", "world"], response=b"hello world"
    )


@pytest.mark.asyncio
async def test_response_parses_set():
    assert await response.parse(
        "*3\r\n$3\r\nset\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
    ) == ParsedCommand(command=Command.Set, args=["foo", "bar"], response="OK")


@pytest.mark.asyncio
async def test_response_parses_get_missing_key():
    result = await response.parse("*2\r\n$3\r\nget\r\n$14\r\nno_such_key_99\r\n")
    assert result.command == Command.Get
    assert result.response is None


@pytest.mark.asyncio
async def test_response_parses_get_existing_key():
    await response.parse("*3\r\n$3\r\nset\r\n$3\r\nbaz\r\n$3\r\nqux\r\n")
    result = await response.parse("*2\r\n$3\r\nget\r\n$3\r\nbaz\r\n")
    assert result.command == Command.Get
    assert result.response == b"qux"


@pytest.mark.asyncio
async def test_response_parses_replconf():
    assert await response.parse(
        "*3\r\n$8\r\nREPLCONF\r\n$14\r\nlistening-port\r\n$4\r\n6380\r\n"
    ) == ParsedCommand(
        command=Command.Replconf, args=["listening-port", "6380"], response="OK"
    )


@pytest.mark.asyncio
async def test_response_parses_replconf_capa_psync2():
    assert await response.parse(
        "*3\r\n$8\r\nREPLCONF\r\n$4\r\ncapa\r\n$6\r\npsync2\r\n"
    ) == ParsedCommand(command=Command.Replconf, args=["capa", "psync2"], response="OK")


@pytest.mark.asyncio
async def test_response_non_array_raises():
    with pytest.raises(RESPParseError):
        await response.parse("+OK\r\n")


@pytest.mark.asyncio
async def test_response_unknown_command_raises():
    with pytest.raises(RuntimeError):
        await response.parse("*1\r\n$7\r\nunknown\r\n")


@pytest.mark.asyncio
async def test_response_parses_info():
    result = await response.parse("*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n")
    assert result.command == Command.Info
    assert b"role" in result.response


@pytest.mark.asyncio
async def test_response_parses_psync():
    result = await response.parse("*3\r\n$5\r\nPSYNC\r\n$1\r\n?\r\n$2\r\n-1\r\n")
    assert result.command == Command.Psync
    assert "FULLRESYNC" in result.response


@pytest.mark.asyncio
async def test_response_parses_wait():
    from app.replica import replication

    replication.REPLICA_STREAMS.clear()
    result = await response.parse("*3\r\n$4\r\nWAIT\r\n$1\r\n1\r\n$3\r\n500\r\n")
    assert result.command == Command.Wait
    assert result.response == 0
