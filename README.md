[![MyRedis CI](https://github.com/Varaprasad091/myredis/actions/workflows/ci.yml/badge.svg)](https://github.com/Varaprasad091/myredis/actions/workflows/ci.yml)
# MyRedis

A lightweight Redis-compatible in-memory key-value database/server built from scratch in Python.

The project was designed to understand the internals of backend systems, networking, databases, concurrency, persistence, caching and distributed systems.

---

## Features

- TCP server
- RESP-compatible request parsing
- Concurrent client handling
- Thread-safe in-memory key-value store
- `SET`, `GET`, `DEL`
- `PING`
- TTL / key expiration
- LRU eviction
- AOF persistence
- RDB snapshots
- Pub/Sub
- Primary → replica replication
- Runtime configuration through environment variables
- Runtime metrics through `INFO`
- Graceful shutdown
- Persistence recovery
- Automated tests
- Docker support
- Performance benchmarking

---

## Architecture

```text
                         Redis Client
                              |
                              | TCP / RESP
                              v
                    +--------------------+
                    |     TCP Server     |
                    +--------------------+
                              |
                              v
                    +--------------------+
                    |    Connection      |
                    |  Client Handling   |
                    +--------------------+
                              |
                              v
                    +--------------------+
                    |  Command Handler   |
                    +--------------------+
                       /      |       \
                      /       |        \
                     v        v         v
              +---------+  +------+  +---------+
              |  Store  |  | AOF  |  | Pub/Sub |
              +---------+  +------+  +---------+
                  |
          +-------+-------+
          |               |
          v               v
       TTL / Expiry    LRU Eviction
          |
          v
       RDB Snapshot

                    Primary
                       |
                       | Replication
                       v
                    Replica