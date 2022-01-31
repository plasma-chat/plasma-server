# Plasma Server

The server software for Plasma. Follow up of [this README](https://github.com/plasma-chat/plasma).  
This guide assumes you already have a `plasma-server` folder and are in it.

### Configuration

Before you can launch the server, you first need to make a `config.json` file.  
To ease this process, a `config.ex.json` file already exists, rename it to `config.json`.

The average server `config.json` would look like this:
```json
{
    "name": "Server Name",
    "host": "0.0.0.0",
    "port": 42080,
    "max_file_size": 5,
    "max_msg_len": 400
}

```

Pretty simple, right? Here's a basic explanation:
- `name` - The name of the server, default is `Unnamed Server`
- `host` - The host to bind to, default is `localhost`
- `port` - The port to bind to, default is `42080`
- `max_file_size` - The maximum filesize in mb allowed for uploads, default is `5`
- `max_msg_len` - The maximum length of a message, default is `400`

### Launching

The server can simply be launched by calling `server.py`.  
Currently, no server flags are available, although this README will be updated if some are added.
