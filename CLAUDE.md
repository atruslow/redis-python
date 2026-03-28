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

**Linting:**
```sh
ruff check . --fix
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
1. `app/main.py:handle_client` — calls `parse_stream(reader)` to read one complete RESP array frame
2. `app/response.py:parse_command` — dispatches to per-command handlers based on `Command` enum
3. Command handler returns a `ParsedCommand(command, args, response)` dataclass
4. `ParsedCommand.encode()` calls `resp_parser.encode()` and writes `bytes` back to the socket
5. `app/main.py:_handle_replication` — after each command, registers replica writers (PSYNC) or propagates to replicas (SET)

**Key modules:**
- `app/command/const.py` — `Command` (`StrEnum` with `auto()`, value = lowercase name), `ParsedCommand` dataclass; `encode()` delegates to `resp_parser`; `original_command` re-encodes as RESP array of bulk strings; `replication_response` flag controls whether replica responds back to master
- `app/command/set.py` / `get.py` — SET (with EX/PX expiry parsed as option pairs) and GET handlers
- `app/command/info.py` — INFO/PSYNC support; `init_info(**kwargs)` called once at startup, `get_info()` used by handlers; holds `ReplicationInfo` dataclass with `master_repl_offset` and `is_slave` property
- `app/cache/cache.py` — in-memory `CACHE` dict of `CacheItem` objects with optional UTC expiry; expiry is checked lazily on GET
- `app/parser/parser.py` — full RESP2 parser and encoder; `parse(bytes)` returns `(RESPValue, bytes_consumed)`, `encode(RESPValue)` returns `bytes`; `parse_stream(reader)` reads one complete RESP array from an asyncio StreamReader
- `app/replica/handshake.py` — replica handshake sequence (PING → REPLCONF listening-port → REPLCONF capa → PSYNC → consume RDB)
- `app/replica/replication.py` — master side: `REPLICA_STREAMS` set, `send_replication` propagates write commands; replica side: `receive_replication` reads commands from master, increments offset, responds only to GETACK

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
- Run `ruff check . --fix` before committing
- Run pytest before commiting, wih coverage
  - Don't commit with lower than 90% test coverage
- Run `mypy .` to check types — all files must pass cleanly
- Docstrings: don't use block comment separators (`# ---`), use Python docstrings; every public function and class should have a docstring
- Tests: write flat top-level functions (`def test_foo`), not classes, unless there's a specific reason to group (e.g. shared fixtures via `setup_method`)

## Codecrafter Instructions

See `instructions.md` for the current codecrafters challenge.
