from persistence.aof import AOF
from replication.replica import ReplicaClient
from persistence.rdb import RDB
from config import Config


class CommandHandler:
    def __init__(
        self,
        store,
        pubsub,
        connection,
        metrics
    ):
        self.store = store

        self.aof = AOF()
        self.rdb = RDB()

        self.pubsub = pubsub
        self.connection = connection
        self.metrics = metrics

        if Config.REPLICATION_ENABLED:
            self.replica = ReplicaClient(
                host=Config.REPLICA_HOST,
                port=Config.REPLICA_PORT
            )
        else:
            self.replica = None

    def handle(self, command):

        if not command:
            return b"-ERR empty command\r\n"

        name = command[0].upper()

        # -------------------------
        # PING
        # -------------------------

        if name == "PING":
            return b"+PONG\r\n"

        # -------------------------
        # SET
        # -------------------------

        if name == "SET":

            if len(command) == 3:

                key = command[1]
                value = command[2]

                self.store.set(
                    key,
                    value
                )
                if Config.PERSISTENCE_ENABLED:
                    self.aof.append(command)

                if self.replica is not None:
                    self.replica.replicate(command)

                return b"+OK\r\n"

            if (
                len(command) == 5
                and command[3].upper() == "EX"
            ):

                key = command[1]
                value = command[2]

                try:
                    ttl = int(command[4])
                except ValueError:
                    return (
                        b"-ERR invalid "
                        b"expiration time\r\n"
                    )

                if ttl <= 0:
                    return (
                        b"-ERR invalid "
                        b"expiration time\r\n"
                    )

                self.store.set(
                    key,
                    value,
                    ttl
                )
                if Config.PERSISTENCE_ENABLED:
                  self.aof.append(command)

                if self.replica is not None:
                    self.replica.replicate(command)

                return b"+OK\r\n"

            return b"-ERR syntax error\r\n"

        # -------------------------
        # GET
        # -------------------------

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

                self.metrics.cache_miss()

                return b"$-1\r\n"

            self.metrics.cache_hit()

            value_bytes = value.encode()

            return (
                b"$"
                + str(len(value_bytes)).encode()
                + b"\r\n"
                + value_bytes
                + b"\r\n"
            )

        # -------------------------
        # DEL
        # -------------------------

        if name == "DEL":

            if len(command) != 2:
                return (
                    b"-ERR wrong number of arguments "
                    b"for DEL\r\n"
                )

            deleted = self.store.delete(
                command[1]
            )

            if deleted:

                self.aof.append(command)

                if self.replica is not None:
                    self.replica.replicate(command)

            return (
                b":1\r\n"
                if deleted
                else b":0\r\n"
            )

        # -------------------------
        # SAVE
        # -------------------------

        if name == "SAVE":

            self.rdb.save(
                self.store.data,
                self.store.expiry
            )

            return b"+OK\r\n"

        # -------------------------
        # SUBSCRIBE
        # -------------------------

        if name == "SUBSCRIBE":

            if len(command) != 2:
                return (
                    b"-ERR wrong number of arguments "
                    b"for SUBSCRIBE\r\n"
                )

            channel = command[1]

            self.pubsub.subscribe(
                channel,
                self.connection
            )

            channel_bytes = channel.encode()

            return (
                b"*3\r\n"
                b"$9\r\nsubscribe\r\n"
                b"$"
                + str(len(channel_bytes)).encode()
                + b"\r\n"
                + channel_bytes
                + b"\r\n"
                b":1\r\n"
            )

        # -------------------------
        # UNSUBSCRIBE
        # -------------------------

        if name == "UNSUBSCRIBE":

            if len(command) != 2:
                return (
                    b"-ERR wrong number of arguments "
                    b"for UNSUBSCRIBE\r\n"
                )

            channel = command[1]

            self.pubsub.unsubscribe(
                channel,
                self.connection
            )

            channel_bytes = channel.encode()

            return (
                b"*3\r\n"
                b"$11\r\nunsubscribe\r\n"
                b"$"
                + str(len(channel_bytes)).encode()
                + b"\r\n"
                + channel_bytes
                + b"\r\n"
                b":0\r\n"
            )

        # -------------------------
        # PUBLISH
        # -------------------------

        if name == "PUBLISH":

            if len(command) != 3:
                return (
                    b"-ERR wrong number of arguments "
                    b"for PUBLISH\r\n"
                )

            channel = command[1]
            message = command[2]

            count = self.pubsub.publish(
                channel,
                message
            )

            return (
                b":"
                + str(count).encode()
                + b"\r\n"
            )

        # -------------------------
        # INFO
        # -------------------------

        if name == "INFO":

            metrics = self.metrics.snapshot()

            response = (
                f"connected_clients:"
                f"{metrics['connected_clients']}\r\n"

                f"commands_processed:"
                f"{metrics['commands_processed']}\r\n"

                f"cache_hits:"
                f"{metrics['cache_hits']}\r\n"

                f"cache_misses:"
                f"{metrics['cache_misses']}\r\n"

                f"evictions:"
                f"{metrics['evictions']}\r\n"

                f"expired_keys:"
                f"{metrics['expired_keys']}\r\n"
            )

            response_bytes = response.encode()

            return (
                b"$"
                + str(len(response_bytes)).encode()
                + b"\r\n"
                + response_bytes
                + b"\r\n"
            )

        # -------------------------
        # UNKNOWN
        # -------------------------

        return b"-ERR unknown command\r\n"