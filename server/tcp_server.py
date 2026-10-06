import socket
import threading
import time

from core.store import Store
from server.connection import Connection
from persistence.aof import AOF
from persistence.rdb import RDB
from pubsub.pubsub import PubSub
from core.metrics import Metrics
from config import Config


class TCPServer:
    def __init__(self, host=None, port=None):
        self.host = host or Config.HOST
        self.port = port or Config.PORT

        self.server_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        # Metrics
        self.metrics = Metrics()

        # Shared in-memory store
        # Metrics are attached only after persistence recovery
        # so recovery operations are not counted as runtime events.
        self.store = Store(
            max_memory=Config.MAX_MEMORY
        )

        self.aof = AOF()
        self.rdb = RDB()
        self.pubsub = PubSub()

        # Track active connections
        self.connections = set()
        self.connections_lock = threading.RLock()

        # Server state
        self.running = True

        # Recover persisted data
        self._load_rdb()
        self._load_aof()

        # Start runtime metrics after recovery
        self.store.metrics = self.metrics

    def _load_rdb(self):
        snapshot = self.rdb.load()

        data = snapshot.get("data", {})
        expiry = snapshot.get("expiry", {})

        loaded = 0

        for key, value in data.items():

            if key in expiry:

                remaining_ttl = (
                    expiry[key] - time.time()
                )

                if remaining_ttl <= 0:
                    continue

                self.store.set(
                    key,
                    value,
                    remaining_ttl
                )

            else:

                self.store.set(
                    key,
                    value
                )

            loaded += 1

        print(
            f"RDB recovery: loaded {loaded} keys"
        )

    def _load_aof(self):
        commands = self.aof.load()

        loaded = 0

        for command in commands:

            if not command:
                continue

            name = command[0].upper()

            # SET
            if name == "SET":

                # SET key value
                if len(command) == 3:

                    self.store.set(
                        command[1],
                        command[2]
                    )

                    loaded += 1

                # SET key value EXAT timestamp
                elif (
                    len(command) == 5
                    and command[3].upper() == "EXAT"
                ):

                    try:
                        expire_at = int(command[4])
                    except ValueError:
                        continue

                    remaining_ttl = (
                        expire_at - int(time.time())
                    )

                    if remaining_ttl <= 0:
                        continue

                    self.store.set(
                        command[1],
                        command[2],
                        remaining_ttl
                    )

                    loaded += 1

            # DEL
            elif name == "DEL":

                if len(command) == 2:

                    self.store.delete(
                        command[1]
                    )

                    loaded += 1

        print(
            f"AOF recovery: loaded {loaded} commands"
        )

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

        # Allow accept() to periodically check
        # whether shutdown was requested.
        self.server_socket.settimeout(1.0)

        print(
            f"MyRedis listening on "
            f"{self.host}:{self.port}"
        )

        try:

            while self.running:

                try:
                    client_socket, client_address = (
                        self.server_socket.accept()
                    )

                except socket.timeout:
                    continue

                except OSError:

                    if not self.running:
                        break

                    raise

                print(
                    f"Client connected: "
                    f"{client_address}"
                )

                connection = Connection(
                    client_socket,
                    client_address,
                    self.store,
                    self.pubsub,
                    self.metrics
                )

                with self.connections_lock:
                    self.connections.add(connection)

                client_thread = threading.Thread(
                    target=self._handle_connection,
                    args=(connection,),
                    daemon=True
                )

                client_thread.start()

        except KeyboardInterrupt:

            print("\nShutdown requested")

        finally:
            self.shutdown()

    def _handle_connection(self, connection):

        try:
            connection.handle()

        finally:

            with self.connections_lock:
                self.connections.discard(connection)

    def shutdown(self):

        if not self.running:
            return

        print("Shutting down MyRedis...")

        self.running = False

        # Stop accepting new clients
        try:
            self.server_socket.close()
        except OSError:
            pass

        # Stop active client connections
        with self.connections_lock:
            connections = list(self.connections)

        for connection in connections:
            connection.stop()

        print(
            f"Closed {len(connections)} active connections"
        )


        print("MyRedis shutdown complete")