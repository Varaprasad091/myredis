import os
import time


class AOF:
    def __init__(self, filename=None):
        self.filename = filename or os.getenv(
            "MYREDIS_AOF_FILE",
            "appendonly.aof"
        )

    def append(self, command):
        command = list(command)

        if (
            len(command) == 5
            and command[0].upper() == "SET"
            and command[3].upper() == "EX"
        ):
            try:
                ttl = int(command[4])
            except ValueError:
                return

            expire_at = int(time.time()) + ttl

            command = [
                command[0],
                command[1],
                command[2],
                "EXAT",
                str(expire_at)
            ]

        with open(
            self.filename,
            "a",
            encoding="utf-8"
        ) as file:
            file.write(" ".join(command) + "\n")

    def load(self):
        if not os.path.exists(self.filename):
            return []

        commands = []

        with open(
            self.filename,
            "r",
            encoding="utf-8"
        ) as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                commands.append(line.split())

        return commands