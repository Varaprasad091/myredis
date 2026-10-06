import socket
import threading
import time
import statistics


HOST = "127.0.0.1"

MYREDIS_PORT = 6390
REDIS_PORT = 6380

CLIENT_LEVELS = [1, 10, 50]

REQUESTS_PER_CLIENT = 100

TOTAL_KEYS = 10000


def build_command(*parts):
    request = f"*{len(parts)}\r\n"

    for part in parts:
        part = str(part)

        request += (
            f"${len(part)}\r\n"
            f"{part}\r\n"
        )

    return request.encode()


def send_command(sock, *parts):
    sock.sendall(
        build_command(*parts)
    )

    return sock.recv(4096)


def percentile(values, percentage):
    if not values:
        return 0.0

    values = sorted(values)

    index = int(
        (percentage / 100) * len(values)
    )

    if index >= len(values):
        index = len(values) - 1

    return values[index]


def run_worker(
    client_id,
    port,
    workload,
    latencies,
    errors
):
    try:

        with socket.create_connection(
            (HOST, port),
            timeout=5
        ) as sock:

            for request_id in range(
                REQUESTS_PER_CLIENT
            ):

                key_id = (
                    client_id
                    * REQUESTS_PER_CLIENT
                    + request_id
                ) % TOTAL_KEYS

                key = f"bench_{key_id}"
                value = f"value_{key_id}"

                if workload == "SET":

                    command = (
                        "SET",
                        key,
                        value
                    )

                    expected = b"+OK\r\n"

                elif workload == "GET":

                    command = (
                        "GET",
                        key
                    )

                    expected = None

                else:

                    # 50% SET / 50% GET
                    if request_id % 2 == 0:

                        command = (
                            "SET",
                            key,
                            value
                        )

                        expected = b"+OK\r\n"

                    else:

                        command = (
                            "GET",
                            key
                        )

                        expected = None

                start = time.perf_counter()

                response = send_command(
                    sock,
                    *command
                )

                end = time.perf_counter()

                if expected is not None:
                    if response != expected:
                        raise RuntimeError(
                            f"Unexpected response: "
                            f"{response!r}"
                        )

                else:
                    if not (
                        response.startswith(b"$")
                    ):
                        raise RuntimeError(
                            f"Unexpected GET response: "
                            f"{response!r}"
                        )

                latencies.append(
                    (end - start) * 1000
                )

    except Exception as error:

        errors.append(error)


def benchmark(
    name,
    port,
    workload,
    clients
):
    total_requests = (
        clients
        * REQUESTS_PER_CLIENT
    )

    latencies = []
    errors = []
    threads = []

    start_time = time.perf_counter()

    for client_id in range(clients):

        thread = threading.Thread(
            target=run_worker,
            args=(
                client_id,
                port,
                workload,
                latencies,
                errors
            )
        )

        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.perf_counter()

    total_time = (
        end_time - start_time
    )

    successful = len(latencies)

    if successful == 0:
        return {
            "successful": 0,
            "failed": len(errors),
            "throughput": 0,
            "average": 0,
            "p50": 0,
            "p95": 0,
            "p99": 0,
            "min": 0,
            "max": 0,
        }

    return {
        "successful": successful,
        "failed": len(errors),
        "throughput": (
            successful / total_time
        ),
        "average": statistics.mean(
            latencies
        ),
        "p50": percentile(
            latencies,
            50
        ),
        "p95": percentile(
            latencies,
            95
        ),
        "p99": percentile(
            latencies,
            99
        ),
        "min": min(latencies),
        "max": max(latencies),
    }


def print_result(
    name,
    workload,
    clients,
    result
):
    print()
    print(
        f"{name} | "
        f"{workload} | "
        f"{clients} clients"
    )

    print("-" * 55)

    print(
        f"Successful : "
        f"{result['successful']}"
    )

    print(
        f"Failed     : "
        f"{result['failed']}"
    )

    print(
        f"Throughput : "
        f"{result['throughput']:.2f} ops/sec"
    )

    print(
        f"Average    : "
        f"{result['average']:.3f} ms"
    )

    print(
        f"p50        : "
        f"{result['p50']:.3f} ms"
    )

    print(
        f"p95        : "
        f"{result['p95']:.3f} ms"
    )

    print(
        f"p99        : "
        f"{result['p99']:.3f} ms"
    )

    print(
        f"Min        : "
        f"{result['min']:.3f} ms"
    )

    print(
        f"Max        : "
        f"{result['max']:.3f} ms"
    )


def main():

    print()
    print("==========================================")
    print("       MyRedis vs Redis Benchmark")
    print("==========================================")

    print()
    print(
        f"MyRedis : {HOST}:{MYREDIS_PORT}"
    )

    print(
        f"Redis   : {HOST}:{REDIS_PORT}"
    )

    print()
    print(
        f"Requests/client : "
        f"{REQUESTS_PER_CLIENT}"
    )

    print(
        f"Client levels   : "
        f"{CLIENT_LEVELS}"
    )

    workloads = [
        "SET",
        "GET",
        "MIXED",
    ]

    all_results = []

    for workload in workloads:

        for clients in CLIENT_LEVELS:

            print()
            print("=" * 60)

            print(
                f"Workload: {workload}"
            )

            print(
                f"Concurrency: "
                f"{clients} clients"
            )

            print("=" * 60)

            # -------------------------
            # MyRedis
            # -------------------------

            myredis = benchmark(
                "MyRedis",
                MYREDIS_PORT,
                workload,
                clients
            )

            print_result(
                "MyRedis",
                workload,
                clients,
                myredis
            )

            # -------------------------
            # Redis
            # -------------------------

            redis = benchmark(
                "Redis",
                REDIS_PORT,
                workload,
                clients
            )

            print_result(
                "Redis",
                workload,
                clients,
                redis
            )

            all_results.append(
                (
                    workload,
                    clients,
                    myredis,
                    redis
                )
            )

    # -------------------------
    # Final comparison
    # -------------------------

    print()
    print()
    print("==========================================")
    print("             FINAL SUMMARY")
    print("==========================================")

    print()

    print(
        f"{'Workload':<10}"
        f"{'Clients':>8}"
        f"{'MyRedis':>14}"
        f"{'Redis':>14}"
        f"{'Ratio':>10}"
    )

    print("-" * 60)

    for (
        workload,
        clients,
        myredis,
        redis
    ) in all_results:

        myredis_throughput = (
            myredis["throughput"]
        )

        redis_throughput = (
            redis["throughput"]
        )

        if myredis_throughput > 0:
            ratio = (
                redis_throughput
                / myredis_throughput
            )
        else:
            ratio = 0

        print(
            f"{workload:<10}"
            f"{clients:>8}"
            f"{myredis_throughput:>14.2f}"
            f"{redis_throughput:>14.2f}"
            f"{ratio:>9.2f}x"
        )


if __name__ == "__main__":
    main()