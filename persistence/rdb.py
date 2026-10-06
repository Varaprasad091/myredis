import os
import pickle


class RDB:
    def __init__(self, filename=None):
        self.filename = filename or os.getenv(
            "MYREDIS_RDB_FILE",
            "dump.rdb"
        )

    def save(self, data, expiry):
        snapshot = {
            "data": dict(data),
            "expiry": dict(expiry)
        }

        with open(self.filename, "wb") as file:
            pickle.dump(snapshot, file)

    def load(self):
        if not os.path.exists(self.filename):
            return {
                "data": {},
                "expiry": {}
            }

        with open(self.filename, "rb") as file:
            snapshot = pickle.load(file)

        # Backward compatibility with old RDB format
        if "data" not in snapshot:
            return {
                "data": snapshot,
                "expiry": {}
            }

        return snapshot