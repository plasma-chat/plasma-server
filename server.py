# Copyright 2022 iiPython

# Modules
import os
import json
import socket
from threading import Thread
from src.client import Client
from src.config import config
from iipython import Connection

# Initialization
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(1, socket.SO_REUSEADDR, 1)
sock.bind((config.get("host", "localhost"), config.get("port", 42080)))
sock.listen(5)

# Server class
class Server(object):
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.clients = []

        # Load history
        try:
            with open("history.db", "r") as f:
                self.history = json.loads(f.read())

        except Exception:
            self.history = []

    def to_dict(self) -> dict:
        return {
            "name": config.get("name", "Untitled Server"),
            "users": [c.attr for c in self.clients if c.attr]
        }

    def broadcast(self, data: dict) -> None:
        for client in self.clients:
            try:
                client.sock.sendjson(data)

            except Exception:
                client.shutdown()

        # Handle history
        if len(self.history) == 50:
            self.history = self.history[1:] = [data]

        else:
            self.history.append(data)

        self.dump_history()

    def dump_history(self) -> None:
        with open("history.db", "w+") as f:
            f.write(json.dumps(self.history))

    def listen(self) -> None:
        while True:
            conn, addr = self.sock.accept()
            client = Client(self, addr, Connection(conn))
            Thread(target = client.loop).start()
            self.clients.append(client)

# Client loop
server = Server(sock)
try:
    server.listen()

except KeyboardInterrupt:
    server.dump_history()
    os._exit(0)
