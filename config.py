import os


class Config:
    HOST = os.getenv(
        "MYREDIS_HOST",
        "0.0.0.0"
    )

    PORT = int(
        os.getenv(
            "MYREDIS_PORT",
            "6379"
        )
    )

    MAX_MEMORY = int(
        os.getenv(
            "MYREDIS_MAX_MEMORY",
            "3"
        )
    )

    AOF_FILE = os.getenv(
        "MYREDIS_AOF_FILE",
        "appendonly.aof"
    )

    RDB_FILE = os.getenv(
        "MYREDIS_RDB_FILE",
        "dump.rdb"
    )

    REPLICATION_ENABLED = (
        os.getenv(
            "MYREDIS_REPLICATION_ENABLED",
            "true"
        ).lower()
        == "true"
    )

    REPLICA_HOST = os.getenv(
        "MYREDIS_REPLICA_HOST",
        "127.0.0.1"
    )

    REPLICA_PORT = int(
        os.getenv(
            "MYREDIS_REPLICA_PORT",
            "6380"
        )
    )

    PERSISTENCE_ENABLED = (
        os.getenv(
            "MYREDIS_PERSISTENCE_ENABLED",
            "true"
        ).lower()
        == "true"
    )