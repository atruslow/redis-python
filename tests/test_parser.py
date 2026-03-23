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
    parse_str,
)


# ---------------------------------------------------------------------------
# Parser — Simple String
# ---------------------------------------------------------------------------

class TestParseSimpleString:
    def test_ok(self):
        value, consumed = parse(b"+OK\r\n")
        assert value == "OK"
        assert consumed == 5

    def test_empty(self):
        value, consumed = parse(b"+\r\n")
        assert value == ""
        assert consumed == 3

    def test_with_spaces(self):
        value, _ = parse(b"+hello world\r\n")
        assert value == "hello world"


# ---------------------------------------------------------------------------
# Parser — Error
# ---------------------------------------------------------------------------

class TestParseError:
    def test_basic(self):
        value, consumed = parse(b"-ERR unknown command\r\n")
        assert isinstance(value, RESPError)
        assert value.message == "ERR unknown command"
        assert consumed == 22

    def test_str_representation(self):
        err = RESPError("WRONGTYPE")
        assert str(err) == "WRONGTYPE"


# ---------------------------------------------------------------------------
# Parser — Integer
# ---------------------------------------------------------------------------

class TestParseInteger:
    def test_positive(self):
        value, consumed = parse(b":42\r\n")
        assert value == 42
        assert consumed == 5

    def test_zero(self):
        value, _ = parse(b":0\r\n")
        assert value == 0

    def test_negative(self):
        value, _ = parse(b":-1\r\n")
        assert value == -1

    def test_invalid(self):
        with pytest.raises(RESPParseError):
            parse(b":abc\r\n")


# ---------------------------------------------------------------------------
# Parser — Bulk String
# ---------------------------------------------------------------------------

class TestParseBulkString:
    def test_basic(self):
        value, consumed = parse(b"$5\r\nhello\r\n")
        assert value == b"hello"
        assert consumed == 11

    def test_empty(self):
        value, consumed = parse(b"$0\r\n\r\n")
        assert value == b""
        assert consumed == 6

    def test_null(self):
        value, consumed = parse(b"$-1\r\n")
        assert value is None
        assert consumed == 5

    def test_binary_safe(self):
        value, _ = parse(b"$3\r\nf\x00o\r\n")
        assert value == b"f\x00o"

    def test_incomplete_raises(self):
        with pytest.raises(RESPParseError):
            parse(b"$5\r\nhel")


# ---------------------------------------------------------------------------
# Parser — Array
# ---------------------------------------------------------------------------

class TestParseArray:
    def test_basic(self):
        value, _ = parse(b"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")
        assert value == [b"foo", b"bar"]

    def test_empty_array(self):
        value, consumed = parse(b"*0\r\n")
        assert value == []
        assert consumed == 4

    def test_null_array(self):
        value, consumed = parse(b"*-1\r\n")
        assert value is None
        assert consumed == 5

    def test_mixed_types(self):
        data = b"*3\r\n+OK\r\n:100\r\n$4\r\ntest\r\n"
        value, _ = parse(data)
        assert value == ["OK", 100, b"test"]

    def test_nested_array(self):
        inner = b"*2\r\n:1\r\n:2\r\n"
        outer = b"*1\r\n" + inner
        value, _ = parse(outer)
        assert value == [[1, 2]]


# ---------------------------------------------------------------------------
# Parser — parse_str
# ---------------------------------------------------------------------------

class TestParseStr:
    def test_simple_string(self):
        assert parse_str("+OK\r\n") == "OK"

    def test_bulk_string(self):
        assert parse_str("$5\r\nhello\r\n") == b"hello"

    def test_array(self):
        assert parse_str("*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n") == [b"foo", b"bar"]

    def test_invalid_raises(self):
        with pytest.raises(RESPParseError):
            parse_str("@bad\r\n")


# ---------------------------------------------------------------------------
# Parser — parse_all
# ---------------------------------------------------------------------------

class TestParseAll:
    def test_two_commands(self):
        data = b"+PONG\r\n+OK\r\n"
        values = parse_all(data)
        assert values == ["PONG", "OK"]

    def test_single_value(self):
        assert parse_all(b":7\r\n") == [7]

    def test_empty_bytes(self):
        assert parse_all(b"") == []


# ---------------------------------------------------------------------------
# Parser — error conditions
# ---------------------------------------------------------------------------

class TestParseErrors:
    def test_empty_input(self):
        with pytest.raises(RESPParseError):
            parse(b"")

    def test_unknown_prefix(self):
        with pytest.raises(RESPParseError):
            parse(b"@unknown\r\n")

    def test_missing_crlf(self):
        with pytest.raises(RESPParseError):
            parse(b"+OK")


# ---------------------------------------------------------------------------
# Encoder — Simple String
# ---------------------------------------------------------------------------

class TestEncodeSimpleString:
    def test_basic(self):
        assert encode("OK") == b"+OK\r\n"

    def test_empty(self):
        assert encode("") == b"+\r\n"

    def test_cr_lf_rejected(self):
        with pytest.raises(ValueError):
            encode("bad\r\nvalue")


# ---------------------------------------------------------------------------
# Encoder — Error
# ---------------------------------------------------------------------------

class TestEncodeError:
    def test_basic(self):
        assert encode(RESPError("ERR bad")) == b"-ERR bad\r\n"


# ---------------------------------------------------------------------------
# Encoder — Integer
# ---------------------------------------------------------------------------

class TestEncodeInteger:
    def test_positive(self):
        assert encode(42) == b":42\r\n"

    def test_zero(self):
        assert encode(0) == b":0\r\n"

    def test_negative(self):
        assert encode(-1) == b":-1\r\n"


# ---------------------------------------------------------------------------
# Encoder — Bulk String
# ---------------------------------------------------------------------------

class TestEncodeBulkString:
    def test_bytes(self):
        assert encode(b"hello") == b"$5\r\nhello\r\n"

    def test_empty_bytes(self):
        assert encode(b"") == b"$0\r\n\r\n"

    def test_null(self):
        assert encode(None) == b"$-1\r\n"

    def test_encode_bulk_string_helper(self):
        assert encode_bulk_string("hello") == b"$5\r\nhello\r\n"


# ---------------------------------------------------------------------------
# Encoder — Array
# ---------------------------------------------------------------------------

class TestEncodeArray:
    def test_basic(self):
        assert encode([b"foo", b"bar"]) == b"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"

    def test_empty(self):
        assert encode([]) == b"*0\r\n"

    def test_mixed_types(self):
        result = encode(["OK", 1, b"data"])
        assert result == b"*3\r\n+OK\r\n:1\r\n$4\r\ndata\r\n"

    def test_nested(self):
        result = encode([[1, 2]])
        assert result == b"*1\r\n*2\r\n:1\r\n:2\r\n"


# ---------------------------------------------------------------------------
# Encoder — unsupported type
# ---------------------------------------------------------------------------

class TestEncodeUnsupported:
    def test_float_raises(self):
        with pytest.raises(TypeError):
            encode(3.14)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:
    @pytest.mark.parametrize("value", [
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
    ])
    def test_round_trip(self, value):
        encoded = encode(value)
        decoded, consumed = parse(encoded)
        assert decoded == value
        assert consumed == len(encoded)

    def test_error_round_trip(self):
        err = RESPError("ERR something went wrong")
        encoded = encode(err)
        decoded, _ = parse(encoded)
        assert isinstance(decoded, RESPError)
        assert decoded.message == err.message
