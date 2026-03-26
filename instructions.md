In this stage, you'll extend your REPLCONF GETACK implementation to respond with the number of bytes of commands processed by the replica.
ACKs (Recap)

As a recap, a master uses ACKs to verify that its replicas are in sync with it and haven't fallen behind. Each ACK contains an offset — the number of bytes of commands processed by the replica.
Offset tracking

A replica keeps its offset updated by tracking the total byte size of every command received from its master. This includes both write commands (like SET, DEL) and non-write commands (like PING, REPLCONF GETACK *).

After processing the received command (e.g., ["SET", "foo", "bar]), it adds the full RESP array byte length to its running offset.

An important rule for this process is that the offset should only include commands processed before the current REPLCONF GETACK * request.

For example:

    A replica connects, completes the handshake, and the master sends REPLCONF GETACK *.
        The replica responds with REPLCONF ACK 0 since no commands had been processed before this request.
    Next, the master sends another REPLCONF GETACK *.
        The replica responds with REPLCONF ACK 37, because the previous REPLCONF command consumed 37 bytes.
    The master then sends a PING command.
        The replica silently processes it, increments its offset by 14, and sends no response.
    The next REPLCONF GETACK * arrives.
        The replica responds with REPLCONF ACK 88 — that’s 37 (for the first REPLCONF), +37 (for the second REPLCONF), +14 (for the PING).

Notice that the current GETACK request itself is not included in the offset value.