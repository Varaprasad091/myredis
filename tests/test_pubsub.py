from pubsub.pubsub import PubSub


class FakeConnection:
    def __init__(self):
        self.messages = []

    def send_message(self, channel, message):
        self.messages.append((channel, message))


def test_subscribe_and_publish():
    pubsub = PubSub()
    connection = FakeConnection()

    pubsub.subscribe("news", connection)

    count = pubsub.publish("news", "hello")

    assert count == 1
    assert connection.messages == [
        ("news", "hello")
    ]


def test_publish_without_subscribers():
    pubsub = PubSub()

    count = pubsub.publish("news", "hello")

    assert count == 0


def test_unsubscribe():
    pubsub = PubSub()
    connection = FakeConnection()

    pubsub.subscribe("news", connection)

    pubsub.unsubscribe("news", connection)

    count = pubsub.publish("news", "hello")

    assert count == 0
    assert connection.messages == []


def test_multiple_subscribers():
    pubsub = PubSub()

    connection1 = FakeConnection()
    connection2 = FakeConnection()

    pubsub.subscribe("news", connection1)
    pubsub.subscribe("news", connection2)

    count = pubsub.publish("news", "hello")

    assert count == 2

    assert connection1.messages == [
        ("news", "hello")
    ]

    assert connection2.messages == [
        ("news", "hello")
    ]


def test_different_channels():
    pubsub = PubSub()

    connection1 = FakeConnection()
    connection2 = FakeConnection()

    pubsub.subscribe("news", connection1)
    pubsub.subscribe("sports", connection2)

    pubsub.publish("news", "news-message")

    assert connection1.messages == [
        ("news", "news-message")
    ]

    assert connection2.messages == []


def test_duplicate_subscription():
    pubsub = PubSub()
    connection = FakeConnection()

    pubsub.subscribe("news", connection)
    pubsub.subscribe("news", connection)

    count = pubsub.publish("news", "hello")

    assert count == 1

    assert connection.messages == [
        ("news", "hello")
    ]
