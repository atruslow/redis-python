Full Resynchronization

When a replica connects to a master for the first time, it sends a PSYNC ? -1 command. This is the replica's way of telling the master that it doesn't have any data yet and needs to be fully resynchronized.

The master responds in two steps:

    It acknowledges with a FULLRESYNC response (Handled in previous stages)
    It sends a snapshot of its current state as an RDB file.

The replica is expected to load the file into memory and replace its current state with the master's data.

For this challenge, you don’t need to build an RDB file yourself. Instead, you can hardcode an empty RDB file, since we’ll assume the master’s database is always empty.

You can find the hex and base64 representation of an empty RDB file here. You need to decode these into binary contents before sending them to the replica.

The file is sent using the following format:

$<length_of_file>\r\n<binary_contents_of_file>

This is similar to how bulk strings are encoded, but without the trailing \r\n.
Tests

The tester will execute your program like this:

./your_program.sh --port <PORT>

It will then connect to your TCP server as a replica and execute the following commands:

    PING - expecting +PONG\r\n
    REPLCONF listening-port <PORT> - expecting +OK\r\n
    REPLCONF capa eof capa psync2 - expecting +OK\r\n
    PSYNC ? -1 - expecting +FULLRESYNC <REPL_ID> 0\r\n

After the last response, the tester will expect to receive an empty RDB file from your server.

The tester will accept any valid RDB file that is empty.
Notes

    The RDB file should be sent like this: $<length>\r\n<contents>
        <length> is the length of the file in bytes
        <contents> is the binary contents of the file
        Note that this is NOT a RESP bulk string and doesn't contain a \r\n at the end.