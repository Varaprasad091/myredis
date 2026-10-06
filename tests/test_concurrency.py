import socket
import threading


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


def worker(index, errors):

    key = f"concurrent_{index}"
    value = f"value_{index}"

    try:
        response = send_command(
            "SET",
            key,
            value
        )

        assert response == b"+OK\r\n"

        response = send_command(
            "GET",
            key
        )

        expected = (
            f"${len(value)}\r\n"
            f"{value}\r\n"
        ).encode()

        assert response == expected

    except Exception as error:
        errors.append(error)


def test_concurrent_clients():

    # Use only 3 keys because Store max_memory = 3.
    errors = []
    threads = []

    for i in range(3):

        thread = threading.Thread(
            target=worker,
            args=(i, errors)
        )

        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    assert not errors, errors