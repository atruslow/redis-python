# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a [CodeCrafters](https://codecrafters.io) challenge project: a toy Redis implementation in Python using `asyncio`. The server is invoked via `spawn_redis_server.sh` (which CodeCrafters uses for testing) and accepts standard Redis wire protocol (RESP).

## Commands

**Run the server:**
```sh
python3 -m app.main -p 6379
python3 -m app.main -p 6380 --replicaof "localhost 6379"  # run as replica
```

**Run tests:**
```sh
python3 -m pytest --cov
python3 -m pytest tests/test_response.py  # single test file
python3 -m pytest -k test_response_parses  # single test by name
```

**Formatting:**
```sh
ruff format
```

**Type checking:**
```sh
mypy .
```

**Manual testing with redis-cli:**
```sh
redis-cli -p 6379 ping
redis-cli -p 6379 set foo bar px 1000
redis-cli -p 6379 get foo
redis-cli -p 6379 info replication
```

## Architecture

The server is single-process, async (asyncio). Each client connection is handled by `handle_client` in `app/main.py`, which reads raw RESP frames, passes them through the parsing pipeline, and writes back the encoded response.

**Request flow:**
1. `app/main.py:handle_client` — reads raw bytes from socket
2. `app/response.py:async_parse` → `parse` — uses `app/parser/parser.py` to parse the RESP frame, decodes bulk-string tokens to `str`
3. `app/response.py:parse_command` — dispatches to per-command handlers based on `Command` enum
4. Command handler returns a `ParsedCommand(command, args, response)` dataclass
5. `ParsedCommand.encode()` calls `resp_parser.encode()` and writes `bytes` back to the socket

**Key modules:**
- `app/command/const.py` — `Command` (`StrEnum` with `auto()`, value = lowercase name), `ParsedCommand` dataclass; `encode()` delegates to `resp_parser`
- `app/command/set.py` / `get.py` — SET (with EX/PX expiry parsed as option pairs) and GET handlers
- `app/command/info.py` — INFO/PSYNC support; `init_info(**kwargs)` called once at startup, `get_info()` used by handlers; holds `ReplicationInfo` dataclass
- `app/cache/cache.py` — in-memory `CACHE` dict of `CacheItem` objects with optional UTC expiry; expiry is checked lazily on GET
- `app/parser/parser.py` — full RESP2 parser and encoder; `parse(bytes)` returns `(RESPValue, bytes_consumed)`, `encode(RESPValue)` returns `bytes`
- `app/replica/handshake.py` — replica handshake sequence (PING → REPLCONF listening-port → REPLCONF capa → PSYNC)

**Adding a new command:**
1. Add a variant to `Command` (`StrEnum`) in `const.py` — the value is automatically the lowercase name
2. Create a handler module under `app/command/` returning a `ParsedCommand`
3. Add a `case` in `parse_command()` in `response.py`

## RESP encoding notes

- `str` response → simple string (`+…\r\n`)
- `bytes` response → bulk string (`$<len>\r\n…\r\n`)
- `None` response → null bulk string (`$-1\r\n`)
- `list` response → array (`*<len>\r\n…`)
- All encoding/decoding goes through `app/parser/parser.py`

## Python Style

- Don't use `assert` outside of tests
- Run `ruff format` before committing
- Run `mypy .` to check types — all files must pass cleanly

## Codecrafter Instructions

See `instructions.md` for the current codecrafters challenge.
