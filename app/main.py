import socket
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 6379), reuse_port=True)
    conn, addr = server_socket.accept() # wait for client

    with conn:
        while True:
            data = conn.recv(1024)
            msg = data.decode()
            if not msg:
                break
            logger.info(f"Received {msg}")
            conn.sendall("+PONG\r\n".encode())
            logger.info("Sent +PONG")


if __name__ == "__main__":
    main()
