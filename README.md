# Redis in Python

A toy Redis server built as part of the [CodeCrafters](https://codecrafters.io) challenge. Implemented in Python using `asyncio`, it speaks the Redis wire protocol (RESP2) and supports both master and replica roles.

I built this with Claude, but did most of the coding and architecture myself. I used Claude for refactoring and debugging.

## Supported Commands

| Command | Notes |
|---|---|
| `PING` | Returns `+PONG` |
| `ECHO <message>` | Returns the message as a bulk string |
| `SET <key> <value> [EX seconds\|PX milliseconds]` | In-memory set with optional expiry |
| `GET <key>` | Returns value or null bulk string |
| `INFO replication` | Returns replication metadata |
| `REPLCONF listening-port <port>` / `capa psync2` | Replica handshake |
| `REPLCONF GETACK *` | Replica responds with current replication offset |
| `PSYNC <replication_id> <offset>` | Returns `+FULLRESYNC <replid> 0` + RDB file |
| `WAIT <numreplicas> <timeout>` | Blocks until N replicas acknowledge all previous writes, or timeout (ms) expires |

## Replication

- Master propagates write commands (SET) to all connected replicas over the replication connection
- Replicas complete the full handshake (PING → REPLCONF → PSYNC), consume the RDB file, then enter a command loop
- Replicas process commands silently — only respond to `REPLCONF GETACK`
- Replication offset tracked on both master and replica
- `WAIT` returns the total number of replicas that have acknowledged all previous writes

## Running

**Master:**
```sh
python3 -m app.main -p 6379
```

**Replica:**
```sh
python3 -m app.main -p 6380 --replicaof "localhost 6379"
```

## Testing

```sh
sh check.sh
```
