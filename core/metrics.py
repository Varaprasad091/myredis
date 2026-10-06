import threading


class Metrics:
    def __init__(self):
        self.lock = threading.RLock()

        self.connected_clients = 0
        self.commands_processed = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.evictions = 0
        self.expired_keys = 0

    def client_connected(self):
        with self.lock:
            self.connected_clients += 1

    def client_disconnected(self):
        with self.lock:
            if self.connected_clients > 0:
                self.connected_clients -= 1

    def command_processed(self):
        with self.lock:
            self.commands_processed += 1

    def cache_hit(self):
        with self.lock:
            self.cache_hits += 1

    def cache_miss(self):
        with self.lock:
            self.cache_misses += 1

    def eviction(self):
        with self.lock:
            self.evictions += 1

    def expired_key(self):
        with self.lock:
            self.expired_keys += 1

    def snapshot(self):
        with self.lock:
            return {
                "connected_clients": self.connected_clients,
                "commands_processed": self.commands_processed,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "evictions": self.evictions,
                "expired_keys": self.expired_keys,
            }