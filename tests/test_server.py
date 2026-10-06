import socket
import time


HOST = "127.0.0.1"
PORT = 6379


def send_command(*parts):
    request = (
        f"*{len(parts)}\r\n"
        + "".join(
            f"${len(str(part))}\r\n{part}\r\n"
            for part in parts
        )
    ).encode()

    with socket.create_connection(
        (HOST, PORT),
        timeout=5
    ) as sock:
        sock.sendall(request)
        return sock.recv(4096)


def test_ping():
    response = send_command("PING")

    assert response == b"+PONG\r\n"


def test_set_get():
    response = send_command(
        "SET",
        "testkey",
        "hello"
    )

    assert response == b"+OK\r\n"

    response = send_command(
        "GET",
        "testkey"
    )

    assert response == b"$5\r\nhello\r\n"


def test_delete():
    send_command(
        "SET",
        "deletekey",
        "hello"
    )

    response = send_command(
        "DEL",
        "deletekey"
    )

    assert response == b":1\r\n"

    response = send_command(
        "GET",
        "deletekey"
    )

    assert response == b"$-1\r\n"


def test_missing_key():
    response = send_command(
        "GET",
        "doesnotexist"
    )

    assert response == b"$-1\r\n"


def test_ttl():
    response = send_command(
        "SET",
        "ttlkey",
        "hello",
        "EX",
        "1"
    )

    assert response == b"+OK\r\n"

    response = send_command(
        "GET",
        "ttlkey"
    )

    assert response == b"$5\r\nhello\r\n"

    time.sleep(1.2)

    response = send_command(
        "GET",
        "ttlkey"
    )

    assert response == b"$-1\r\n"
