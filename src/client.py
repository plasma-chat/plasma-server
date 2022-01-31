# Copyright 2022 iiPython

# Modules
import os
import time
import string
import random
from hashlib import sha256
from src.config import config
from iipython import Connection

# Initialization
_max_filesize = config.get("max_file_size", 5) * (1024 ** 2)
_max_msglength = config.get("max_msg_len", 400)
_files_container = os.path.join(os.path.dirname(__file__), "../files")
if not os.path.isdir(_files_container):
    os.mkdir(_files_container)

# Client class
class Client(object):
    def __init__(self, host, addr: tuple, sock: Connection) -> None:
        self.host, self.addr, self.sock = host, addr, sock
        self.attr = {}

    def make_resp(self, type: str, data: dict = {}) -> dict:
        return {
            "type": type,
            "data": data,
            "server": self.host.to_dict(),
            "ts": time.time()
        }

    def shutdown(self) -> None:
        if self in self.host.clients:
            self.host.clients.remove(self)

        if self.attr:
            self.host.broadcast(self.make_resp("u.leave", {"username": self.attr["username"]}))
            self.attr = {}

        del self

    def loop(self) -> None:
        self.sock.sendjson(self.make_resp("m.history", {"items": self.host.history}))
        while self.sock:
            try:
                events = self.sock.recvjson()
                if not events:
                    break

            except Exception:
                break

            for event in events:
                dtype, data = event.get("type", "").split("."), event.get("data", {})
                if len(dtype) != 2 or not [i.strip() for i in dtype]:
                    self.sock.sendjson(self.make_resp("e.invalid", {"error": "Invalid payload."}))

                elif dtype[0] == "u":
                    if dtype[1] == "identify":
                        if "username" in self.attr:
                            self.sock.sendjson(self.make_resp("e.unexpected", {"error": "You have previously identified yourself."}))
                            continue

                        username = data.get("username", "").strip()
                        for c in [
                            (lambda u: not [c for c in u if c not in string.ascii_letters + string.digits + " _-"], "Username contains invalid characters."),
                            (lambda u: len(u) >= 4 and len(u) <= 16, "Username must be >= 4 <= 16 characters long."),
                            (lambda u: u.lower() not in [c.attr["username"].lower() for c in self.host.clients if c.attr], "The provided username is taken."),
                            (lambda u: u.lower() not in ["system", "server", "admin", "owner", "plasma"], "The specified username is reserved.")
                        ]:
                            if not c[0](username):
                                return self.sock.sendjson(self.make_resp("e.username", {"error": c[1]}))

                        self.attr["username"] = username
                        self.attr["id"] = sha256(f"{self.addr[0]}:{username}".encode("utf8")).hexdigest()
                        self.host.broadcast(self.make_resp("u.join", {"username": username}))

                    elif dtype[1] == "leave":
                        break

                elif dtype[0] == "m":
                    if "username" not in self.attr:
                        self.sock.sendjson(self.make_resp("e.unauthorized", {"error": "You are not identified."}))
                        continue

                    elif dtype[1] == "msg":
                        content = data.get("content", "")
                        if not content:
                            continue

                        elif len(content) > _max_msglength:
                            self.sock.sendjson(self.make_resp("e.overflow", {"error": f"Max message size is {_max_msglength} characters."}))

                        self.host.broadcast(self.make_resp("m.msg", {"content": content, "author": self.attr}))

                    elif dtype[1] == "bin":
                        try:
                            filedata = bytes.fromhex(data["binary"])
                            filename = data["filename"].strip()
                            if [c for c in filename if c in "\\/:;!@#$%^&*()-=_+"] or len(filename) > 32:
                                self.sock.sendjson(self.make_resp("e.invalid", {"error": "Invalid filename."}))
                                continue

                        except Exception:
                            self.sock.sendjson(self.make_resp("e.invalid", {"error": "Invalid payload."}))
                            continue

                        if len(filedata) > _max_filesize:
                            self.sock.sendjson(self.make_resp("e.overflow", {"error": f"File exceeds max file size of {_max_filesize} bytes."}))
                            continue

                        fileid = "".join(random.choice(string.ascii_letters) for i in range(5))
                        with open(os.path.join(_files_container, f"{fileid}_{filename}"), "wb") as f:
                            f.write(filedata)

                        self.host.broadcast(self.make_resp("m.bin", {"filename": filename, "id": fileid, "author": self.attr, "size": len(filedata)}))

                elif dtype[0] == "d":
                    if dtype[1] == "file":
                        fileid = data.get("id", "")
                        if not fileid:
                            self.sock.sendjson(self.make_resp("e.missing", {"error": "Missing file ID."}))
                            continue

                        file = [f for f in os.listdir(_files_container) if f.split("_")[0] == fileid]
                        if not file:
                            self.sock.sendjson(self.make_resp("e.invalid", {"error": "Invalid file ID provided."}))
                            continue

                        with open(os.path.join(_files_container, file[0]), "rb") as f:
                            filedata = f.read().hex()

                        self.sock.sendjson(self.make_resp("d.file", {"filename": "_".join(file[0].split("_")[1:]), "binary": filedata, "callback": data.get("callback")}))

                elif dtype[0] == "_":
                    if dtype[1] == "ping":
                        self.sock.sendjson(self.make_resp("_.ping", {"callback": data.get("callback")}))

        return self.shutdown()
