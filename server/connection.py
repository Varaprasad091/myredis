from server.resp_parser import RESPParser
from core.command_handler import CommandHandler


class Connection:
    def __init__(
        self,
        client_socket,
        client_address,
        store,
        pubsub,
        metrics
    ):
        self.client_socket = client_socket
        self.client_address = client_address

        self.parser = RESPParser()

        self.command_handler = CommandHandler(
            store,
            pubsub,
            self,
            metrics
        )

        self.metrics = metrics

        self.buffer = b""
        self.running = True

        self.client_socket.settimeout(1.0)

        # Metrics
        self.metrics.client_connected()

    def send_message(self, channel, message):
        if not self.running:
            return

        response = (
            b"*3\r\n"
            b"$7\r\nmessage\r\n"
            + b"$"
            + str(len(channel.encode())).encode()
            + b"\r\n"
            + channel.encode()
            + b"\r\n"
            + b"$"
            + str(len(message.encode())).encode()
            + b"\r\n"
            + message.encode()
            + b"\r\n"
        )

        try:
            self.client_socket.sendall(response)

        except (
            ConnectionResetError,
            BrokenPipeError,
            OSError
        ):
            self.running = False

    def stop(self):
        self.running = False

        try:
            self.client_socket.shutdown(2)
        except OSError:
            pass

        try:
            self.client_socket.close()
        except OSError:
            pass

    def handle(self):
        try:
            while self.running:

                try:
                    data = self.client_socket.recv(4096)

                except TimeoutError:
                    continue

                if not data:
                    print(
                        f"Client disconnected: "
                        f"{self.client_address}"
                    )
                    break

                self.buffer += data

                while self.buffer and self.running:

                    result = self.parser.parse(
                        self.buffer
                    )

                    if result is None:
                        break

                    command, consumed = result

                    print(
                        f"Parsed command: {command}"
                    )

                    self.buffer = self.buffer[consumed:]

                    # Metrics
                    self.metrics.command_processed()

                    response = (
                        self.command_handler.handle(
                            command
                        )
                    )

                    self.client_socket.sendall(
                        response
                    )

        except (
            ConnectionResetError,
            BrokenPipeError,
            OSError
        ):
            print(
                f"Client connection lost: "
                f"{self.client_address}"
            )

        except ValueError as error:
            print(
                f"Protocol error: {error}"
            )

        finally:
            self.running = False

            # Metrics
            self.metrics.client_disconnected()

            try:
                self.client_socket.close()
            except OSError:
                pass