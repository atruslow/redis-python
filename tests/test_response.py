from app import response


def test_response_parses():
    assert response.parse("*1\r\n$4\r\nping\r\n") == response.ParsedCommand(
        command=response.Command.Ping, args=[], response=""
    )


def test_respose_parses_echo():
    assert response.parse(
        "*2\r\n$4\r\necho\r\n$3\r\nhey\r\n"
    ) == response.ParsedCommand(
        command=response.Command.Echo, args=["hey"], response="hey"
    )


def test_encode_string():
    encoded_str = response.encode("hey")

    assert encoded_str == "$3\r\nhey\r\n"
