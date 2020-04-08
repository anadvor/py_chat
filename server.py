#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()
        self.server.recent_messages.append(f"<{self.login}>: {decoded}")
        if len(self.server.recent_messages) > 10:
            self.server.recent_messages.pop(0)
        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login_acceptable = True
                for user in self.server.clients:
                    if user.login == decoded.replace("login:", "").replace("\r\n", ""):
                        login_acceptable = False
                if login_acceptable:
                    self.login = decoded.replace("login:", "").replace("\r\n", "")
                    self.transport.write(f"Привет, {self.login}!\n".encode())
                    self.transport.write(f"Вот последние сообщения этого чата:\n".encode())
                    self.send_history()
                else:
                    self.transport.write(f"Данный логин уже занят, выберите другой...\n".encode())

            else:
                self.transport.write(f"Неправильный логин\n".encode())
            
    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"<{self.login}>: {content}\n"
        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):
        for note in self.server.recent_messages:
            self.transport.write(note.encode())


class Server:
    clients: list
    recent_messages: list

    def __init__(self):
        self.clients = []
        self.recent_messages = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()
        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            9999
        )
        print("Сервер запущен...")
        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
