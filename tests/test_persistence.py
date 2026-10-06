import time

from persistence.aof import AOF
from persistence.rdb import RDB


def test_aof_append_and_load(tmp_path):
    filename = tmp_path / "test.aof"

    aof = AOF(str(filename))

    aof.append(["SET", "name", "alice"])
    aof.append(["DEL", "name"])

    commands = aof.load()

    assert commands == [
        ["SET", "name", "alice"],
        ["DEL", "name"],
    ]


def test_aof_ttl_converts_to_exat(tmp_path):
    filename = tmp_path / "test.aof"

    aof = AOF(str(filename))

    before = int(time.time())

    aof.append([
        "SET",
        "temp",
        "hello",
        "EX",
        "10",
    ])

    commands = aof.load()

    after = int(time.time())

    assert len(commands) == 1

    command = commands[0]

    assert command[:4] == [
        "SET",
        "temp",
        "hello",
        "EXAT",
    ]

    expire_at = int(command[4])

    assert before + 10 <= expire_at <= after + 10


def test_aof_load_missing_file(tmp_path):
    filename = tmp_path / "missing.aof"

    aof = AOF(str(filename))

    assert aof.load() == []


def test_rdb_save_and_load(tmp_path):
    filename = tmp_path / "test.rdb"

    rdb = RDB(str(filename))

    data = {
        "name": "alice",
        "city": "hyderabad",
    }

    expiry = {
        "name": 9999999999,
    }

    rdb.save(data, expiry)

    snapshot = rdb.load()

    assert snapshot["data"] == data
    assert snapshot["expiry"] == expiry


def test_rdb_load_missing_file(tmp_path):
    filename = tmp_path / "missing.rdb"

    rdb = RDB(str(filename))

    snapshot = rdb.load()

    assert snapshot == {
        "data": {},
        "expiry": {},
    }


def test_rdb_backward_compatible_format(tmp_path):
    filename = tmp_path / "old.rdb"

    rdb = RDB(str(filename))

    import pickle

    old_data = {
        "key": "value",
    }

    with open(filename, "wb") as file:
        pickle.dump(old_data, file)

    snapshot = rdb.load()

    assert snapshot == {
        "data": old_data,
        "expiry": {},
    }
