class RESPParser:
    def parse(self, data: bytes):
        if not data:
            return None

        if data[0:1] != b"*":
            raise ValueError("Invalid RESP request")

        pos = data.find(b"\r\n")

        if pos == -1:
            return None

        array_length = int(data[1:pos])
        index = pos + 2
        commands = []

        for _ in range(array_length):
            if index >= len(data):
                return None

            if data[index:index + 1] != b"$":
                raise ValueError("Invalid bulk string")

            line_end = data.find(b"\r\n", index)

            if line_end == -1:
                return None

            string_length = int(data[index + 1:line_end])
            index = line_end + 2

            end = index + string_length

            if len(data) < end + 2:
                return None

            command = data[index:end]

            if data[end:end + 2] != b"\r\n":
                raise ValueError("Invalid RESP termination")

            commands.append(command.decode())
            index = end + 2

        return commands, index