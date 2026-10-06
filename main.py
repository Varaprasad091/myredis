from server.tcp_server import TCPServer


def main():
    server = TCPServer()
    server.start()


if __name__ == "__main__":
    main()