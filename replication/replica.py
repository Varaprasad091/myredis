import os
import socket
import threading

from core.store import Store
from server.resp_parser import RESPParser


class Replica:
    def __init__(self, host=None, port=None):
        self.host = host or os.getenv(
            "MYREDIS_REPLICA_HOST",
            "127.0.0.1"
        )

        self.port = int(
            port or os.getenv(
                "MYREDIS_REPLICA_PORT",
                "6380"
            )
        )

        self.server_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        self.store = Store(
            max_memory=3
        )

        self.parser = RESPParser()

    def start(self):
        self.server_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        self.server_socket.bind(
            (self.host, self.port)
        )

        self.server_socket.listen()

        print(
            f"Replica listening on "
            f"{self.host}:{self.port}"
        )

        while True:
            client_socket, client_address = (
                self.server_socket.accept()
            )

            print(
                f"Replica client connected: "
                f"{client_address}"
            )

            thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket,),
                daemon=True
            )

            thread.start()

    def handle_client(self, client_socket):
        buffer = b""

        try:
            while True:
                data = client_socket.recv(4096)

                if not data:
                    break

                buffer += data

                # Process internal replication commands.
                #
                # SET key value
                # SET key value EX seconds
                # DEL key

                while True:

                    if (
                        buffer.startswith(b"SET ")
                        or buffer.startswith(b"DEL ")
                    ):
                        if b"\n" not in buffer:
                            break

                        line, buffer = buffer.split(
                            b"\n",
                            1
                        )

                        command = line.decode().split()

                        print(
                            f"Replica command: "
                            f"{command}"
                        )

                        self.apply_command(command)

                        continue

                    break

                # Process normal client RESP commands.
                while buffer:

                    result = self.parser.parse(buffer)

                    if result is None:
                        break

                    command, consumed = result

                    buffer = buffer[consumed:]

                    print(
                        f"Replica command: "
                        f"{command}"
                    )

                    response = self.handle_command(
                        command
                    )

                    client_socket.sendall(response)

        except (
            ConnectionResetError,
            BrokenPipeError,
            OSError
        ):
            pass

        except ValueError as error:
            print(
                f"Replica protocol error: "
                f"{error}"
            )

        finally:
            try:
                client_socket.close()
            except OSError:
                pass

    def handle_command(self, command):
        if not command:
            return b"-ERR empty command\r\n"

        name = command[0].upper()

        if name == "GET":

            if len(command) != 2:
                return (
                    b"-ERR wrong number of arguments "
                    b"for GET\r\n"
                )

            value = self.store.get(
                command[1]
            )

            if value is None:
                return b"$-1\r\n"

            value_bytes = value.encode()

            return (
                b"$"
                + str(len(value_bytes)).encode()
                + b"\r\n"
                + value_bytes
                + b"\r\n"
            )

        if name == "PING":
            return b"+PONG\r\n"

        return b"-ERR unknown command\r\n"

    def apply_command(self, command):
        if not command:
            return

        name = command[0].upper()

        if name == "SET":

            # SET key value
            if len(command) == 3:

                key = command[1]
                value = command[2]

                self.store.set(
                    key,
                    value
                )

                print(
                    f"Replica stored: "
                    f"{key} = {value}"
                )

            # SET key value EX seconds
            elif (
                len(command) == 5
                and command[3].upper() == "EX"
            ):

                key = command[1]
                value = command[2]

                try:
                    ttl = int(command[4])
                except ValueError:
                    return

                self.store.set(
                    key,
                    value,
                    ttl
                )

                print(
                    f"Replica stored: "
                    f"{key} = {value} "
                    f"(TTL: {ttl}s)"
                )

        elif name == "DEL":

            if len(command) == 2:

                key = command[1]

                deleted = self.store.delete(
                    key
                )

                print(
                    f"Replica DEL {key}: "
                    f"{deleted}"
                )


class ReplicaClient:
    def __init__(self, host=None, port=None):
        self.host = host or os.getenv(
            "MYREDIS_REPLICA_HOST",
            "127.0.0.1"
        )

        self.port = int(
            port or os.getenv(
                "MYREDIS_REPLICA_PORT",
                "6380"
            )
        )

        self.socket = None

        # Commands waiting to be replicated.
        self.backlog = []

    def connect(self):

        if self.socket:
            return True

        try:
            self.socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            self.socket.connect(
                (self.host, self.port)
            )

            print(
                "Connected to replica"
            )

            return True

        except OSError:

            self.socket = None

            print(
                "Replica connection failed"
            )

            return False

    def replicate(self, command):

        # Add command to backlog first.
        self.backlog.append(command)

        # Try to connect to replica.
        if not self.connect():
            return

        try:

            # Send pending commands in order.
            while self.backlog:

                pending_command = (
                    self.backlog[0]
                )

                data = (
                    " ".join(pending_command)
                    + "\n"
                ).encode()

                self.socket.sendall(data)

                print(
                    f"Replicated: "
                    f"{pending_command}"
                )

                # Remove only after
                # successful send.
                self.backlog.pop(0)

        except OSError:

            print(
                "Replica connection lost"
            )

            try:
                self.socket.close()
            except OSError:
                pass

            self.socket = None


if __name__ == "__main__":
    replica = Replica()
    replica.start()