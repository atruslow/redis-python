from app import response
from app.command.const import Command, ParsedCommand


def test_response_parses():
    assert response.parse("*1\r\n$4\r\nping\r\n") == ParsedCommand(
        command=Command.Ping, args=[], response="+PONG\r\n"
    )


def test_respose_parses_echo():
    assert response.parse("*2\r\n$4\r\necho\r\n$3\r\nhey\r\n") == ParsedCommand(
        command=Command.Echo, args=["hey"], response="hey"
    )


def test_encode_string():
    encoded_str = response.encode("hey")

    assert encoded_str == "$3\r\nhey\r\n"
