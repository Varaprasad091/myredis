import threading
import time
from collections import OrderedDict


class NoOpLock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class Store:
    def __init__(self, max_memory=100, metrics=None):
        self.data = OrderedDict()
        self.expiry = {}
        self.max_memory = max_memory
        self.metrics = metrics

        lock_enabled = (
            __import__("os")
            .getenv(
                "MYREDIS_LOCK_ENABLED",
                "true"
            )
            .lower()
            == "true"
        )

        if lock_enabled:
            self.lock = threading.RLock()
        else:
            self.lock = NoOpLock()

    def set(self, key, value, ttl=None):
        with self.lock:
            if key in self.data:
                del self.data[key]

            self.data[key] = value

            if ttl is not None:
                self.expiry[key] = time.time() + ttl
            else:
                self.expiry.pop(key, None)

            self._evict_if_needed()

    def get(self, key):
        with self.lock:
            if key not in self.data:
                return None

            if self._is_expired(key):
                self._delete_key(key)

                if self.metrics is not None:
                    self.metrics.expired_key()

                return None

            value = self.data.pop(key)
            self.data[key] = value

            return value

    def delete(self, key):
        with self.lock:
            if key not in self.data:
                return False

            if self._is_expired(key):
                self._delete_key(key)

                if self.metrics is not None:
                    self.metrics.expired_key()

                return False

            self._delete_key(key)
            return True

    def exists(self, key):
        with self.lock:
            if key not in self.data:
                return False

            if self._is_expired(key):
                self._delete_key(key)

                if self.metrics is not None:
                    self.metrics.expired_key()

                return False

            return True

    def _is_expired(self, key):
        if key not in self.expiry:
            return False

        return time.time() >= self.expiry[key]

    def _delete_key(self, key):
        self.data.pop(key, None)
        self.expiry.pop(key, None)

    def _evict_if_needed(self):
        while len(self.data) > self.max_memory:
            oldest_key, _ = self.data.popitem(last=False)
            self.expiry.pop(oldest_key, None)

            if self.metrics is not None:
                self.metrics.eviction()