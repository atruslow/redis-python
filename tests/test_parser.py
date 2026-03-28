"""
Tests for app.parser.parser — RESP2 parser and encoder.
"""

import pytest

from app.parser.parser import (
    RESPError,
    RESPParseError,
    encode,
    encode_bulk_string,
    parse,
    parse_all,
    parse_list,
    parse_str,
)


def test_parse_simple_string_ok():
    value, consumed = parse(b"+OK\r\n")
    assert value == "OK"
    assert consumed == 5


def test_parse_simple_string_empty():
    value, consumed = parse(b"+\r\n")
    assert value == ""
    assert consumed == 3


def test_parse_simple_string_with_spaces():
    value, _ = parse(b"+hello world\r\n")
    assert value == "hello world"


def test_parse_error_basic():
    value, consumed = parse(b"-ERR unknown command\r\n")
    assert isinstance(value, RESPError)
    assert value.message == "ERR unknown command"
    assert consumed == 22


def test_parse_error_str_representation():
    assert str(RESPError("WRONGTYPE")) == "WRONGTYPE"


def test_parse_integer_positive():
    value, consumed = parse(b":42\r\n")
    assert value == 42
    assert consumed == 5


def test_parse_integer_zero():
    value, _ = parse(b":0\r\n")
    assert value == 0


def test_parse_integer_negative():
    value, _ = parse(b":-1\r\n")
    assert value == -1


def test_parse_integer_invalid():
    with pytest.raises(RESPParseError):
        parse(b":abc\r\n")


def test_parse_bulk_string_basic():
    value, consumed = parse(b"$5\r\nhello\r\n")
    assert value == b"hello"
    assert consumed == 11


def test_parse_bulk_string_empty():
    value, consumed = parse(b"$0\r\n\r\n")
    assert value == b""
    assert consumed == 6


def test_parse_bulk_string_null():
    value, consumed = parse(b"$-1\r\n")
    assert value is None
    assert consumed == 5


def test_parse_bulk_string_binary_safe():
    value, _ = parse(b"$3\r\nf\x00o\r\n")
    assert value == b"f\x00o"


def test_parse_bulk_string_incomplete_raises():
    with pytest.raises(RESPParseError):
        parse(b"$5\r\nhel")


def test_parse_bulk_string_invalid_length():
    with pytest.raises(RESPParseError, match="Invalid bulk string length"):
        parse(b"$abc\r\nhello\r\n")


def test_parse_array_basic():
    value, _ = parse(b"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")
    assert value == [b"foo", b"bar"]


def test_parse_array_empty():
    value, consumed = parse(b"*0\r\n")
    assert value == []
    assert consumed == 4


def test_parse_array_null():
    value, consumed = parse(b"*-1\r\n")
    assert value is None
    assert consumed == 5


def test_parse_array_mixed_types():
    value, _ = parse(b"*3\r\n+OK\r\n:100\r\n$4\r\ntest\r\n")
    assert value == ["OK", 100, b"test"]


def test_parse_array_nested():
    value, _ = parse(b"*1\r\n*2\r\n:1\r\n:2\r\n")
    assert value == [[1, 2]]


def test_parse_array_invalid_count():
    with pytest.raises(RESPParseError, match="Invalid array count"):
        parse(b"*abc\r\n")


def test_parse_str_simple_string():
    assert parse_str("+OK\r\n") == "OK"


def test_parse_str_bulk_string():
    assert parse_str("$5\r\nhello\r\n") == b"hello"


def test_parse_str_array():
    assert parse_str("*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n") == [b"foo", b"bar"]


def test_parse_str_invalid_raises():
    with pytest.raises(RESPParseError):
        parse_str("@bad\r\n")


def test_parse_all_two_commands():
    assert parse_all(b"+PONG\r\n+OK\r\n") == ["PONG", "OK"]


def test_parse_all_single_value():
    assert parse_all(b":7\r\n") == [7]


def test_parse_all_empty_bytes():
    assert parse_all(b"") == []


def test_parse_empty_input_raises():
    with pytest.raises(RESPParseError):
        parse(b"")


def test_parse_unknown_prefix_raises():
    with pytest.raises(RESPParseError):
        parse(b"@unknown\r\n")


def test_parse_missing_crlf_raises():
    with pytest.raises(RESPParseError):
        parse(b"+OK")


def test_parse_list_valid():
    assert parse_list("*2\r\n+foo\r\n+bar\r\n") == ["foo", "bar"]


def test_parse_list_not_array_raises():
    with pytest.raises(ValueError, match="Incorrect Data"):
        parse_list("+OK\r\n")


def test_parse_list_non_string_elements_raises():
    with pytest.raises(ValueError, match="Incorrect Data"):
        parse_list("*1\r\n:42\r\n")


def test_encode_simple_string_basic():
    assert encode("OK") == b"+OK\r\n"


def test_encode_simple_string_empty():
    assert encode("") == b"+\r\n"


def test_encode_simple_string_cr_lf_rejected():
    with pytest.raises(ValueError):
        encode("bad\r\nvalue")


def test_encode_error():
    assert encode(RESPError("ERR bad")) == b"-ERR bad\r\n"


def test_encode_integer_positive():
    assert encode(42) == b":42\r\n"


def test_encode_integer_zero():
    assert encode(0) == b":0\r\n"


def test_encode_integer_negative():
    assert encode(-1) == b":-1\r\n"


def test_encode_bulk_string_bytes():
    assert encode(b"hello") == b"$5\r\nhello\r\n"


def test_encode_bulk_string_empty():
    assert encode(b"") == b"$0\r\n\r\n"


def test_encode_null():
    assert encode(None) == b"$-1\r\n"


def test_encode_bulk_string_helper():
    assert encode_bulk_string("hello") == b"$5\r\nhello\r\n"


def test_encode_array_basic():
    assert encode([b"foo", b"bar"]) == b"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"


def test_encode_array_empty():
    assert encode([]) == b"*0\r\n"


def test_encode_array_mixed_types():
    assert encode(["OK", 1, b"data"]) == b"*3\r\n+OK\r\n:1\r\n$4\r\ndata\r\n"


def test_encode_array_nested():
    assert encode([[1, 2]]) == b"*1\r\n*2\r\n:1\r\n:2\r\n"


def test_encode_unsupported_type_raises():
    with pytest.raises(TypeError):
        encode(3.14)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [
        "OK",
        "hello world",
        42,
        -100,
        0,
        b"binary\x00data",
        b"",
        None,
        ["OK", 1, b"bulk"],
        [b"SET", b"key", b"value"],
    ],
)
def test_round_trip(value):
    encoded = encode(value)
    decoded, consumed = parse(encoded)
    assert decoded == value
    assert consumed == len(encoded)


def test_round_trip_error():
    err = RESPError("ERR something went wrong")
    decoded, _ = parse(encode(err))
    assert isinstance(decoded, RESPError)
    assert decoded.message == err.message
