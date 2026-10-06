import threading


class PubSub:
    def __init__(self):
        self.channels = {}
        self.lock = threading.RLock()

    def subscribe(self, channel, connection):
        with self.lock:
            if channel not in self.channels:
                self.channels[channel] = set()

            self.channels[channel].add(connection)

    def unsubscribe(self, channel, connection):
        with self.lock:
            if channel not in self.channels:
                return

            self.channels[channel].discard(connection)

            if not self.channels[channel]:
                del self.channels[channel]

    def publish(self, channel, message):
        with self.lock:
            subscribers = list(
                self.channels.get(channel, set())
            )

        for connection in subscribers:
            connection.send_message(
                channel,
                message
            )

        return len(subscribers)