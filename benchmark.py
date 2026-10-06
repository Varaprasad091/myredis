import socket
import time
import statistics


HOST = "127.0.0.1"
PORT = 6379

NUM_REQUESTS = 1000
NUM_KEYS = 3


def build_command(*parts):
    request = f"*{len(parts)}\r\n"

    for part in parts:
        part = str(part)
        request += f"${len(part)}\r\n{part}\r\n"

    return request.encode()


def send_command(sock, *parts):
    sock.sendall(build_command(*parts))
    return sock.recv(4096)


def percentile(values, percentile):
    values = sorted(values)

    index = int((percentile / 100) * len(values))

    if index >= len(values):
        index = len(values) - 1

    return values[index]


def benchmark_set():
    latencies = []

    with socket.create_connection((HOST, PORT), timeout=5) as sock:
        for i in range(NUM_REQUESTS):
            key_index = i % NUM_KEYS

            start = time.perf_counter()

            response = send_command(
                sock,
                "SET",
                f"bench_key_{key_index}",
                f"value_{key_index}"
            )

            end = time.perf_counter()

            if response != b"+OK\r\n":
                raise RuntimeError(
                    f"Unexpected SET response: {response!r}"
                )

            latencies.append(
                (end - start) * 1000
            )

    return latencies


def benchmark_get():
    latencies = []

    with socket.create_connection((HOST, PORT), timeout=5) as sock:
        for i in range(NUM_REQUESTS):
            key_index = i % NUM_KEYS

            start = time.perf_counter()

            response = send_command(
                sock,
                "GET",
                f"bench_key_{key_index}"
            )

            end = time.perf_counter()

            expected = (
                f"${len(f'value_{key_index}')}\r\n"
                f"value_{key_index}\r\n"
            ).encode()

            if response != expected:
                raise RuntimeError(
                    f"Unexpected GET response: {response!r}"
                )

            latencies.append(
                (end - start) * 1000
            )

    return latencies


def print_results(name, latencies):
    total_seconds = sum(latencies) / 1000

    throughput = (
        len(latencies) / total_seconds
        if total_seconds > 0
        else 0
    )

    print()
    print(f"{name} Benchmark")
    print("-" * 40)
    print(f"Requests      : {len(latencies)}")
    print(f"Throughput    : {throughput:.2f} ops/sec")
    print(
        f"Average       : "
        f"{statistics.mean(latencies):.3f} ms"
    )
    print(
        f"p50           : "
        f"{percentile(latencies, 50):.3f} ms"
    )
    print(
        f"p95           : "
        f"{percentile(latencies, 95):.3f} ms"
    )
    print(
        f"p99           : "
        f"{percentile(latencies, 99):.3f} ms"
    )
    print(
        f"Min           : "
        f"{min(latencies):.3f} ms"
    )
    print(
        f"Max           : "
        f"{max(latencies):.3f} ms"
    )


def main():
    print("MyRedis Benchmark")
    print("=================")
    print(f"Target        : {HOST}:{PORT}")
    print(f"Requests      : {NUM_REQUESTS}")
    print(f"Keys          : {NUM_KEYS}")

    print("\nRunning SET benchmark...")
    set_latencies = benchmark_set()

    print("Running GET benchmark...")
    get_latencies = benchmark_get()

    print_results("SET", set_latencies)
    print_results("GET", get_latencies)


if __name__ == "__main__":
    main()