# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python WebSocket messaging system that enables named clients to exchange messages through a central server.

## Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install websocket-server websocket-client

# Run server (dev mode - localhost:8000)
python WSServer.py

# Run client with custom name
python WSClient.py <client_name>
# Example: python WSClient.py Alice
```

## Architecture

**Message-based routing system**: Clients register with a name via `DECLARATION` message, then can send `ENVOIE` messages to other named clients. Server maintains a `clients` dict mapping names to WebSocket connections.

**Context configuration**: `Context.dev()` uses localhost:8000, `Context.prod()` uses 192.168.4.230:9000.

**Message protocol** (JSON):
```json
{
  "message_type": "declaration|envoie",
  "data": {
    "emitter": "<sender_name>",
    "receiver": "<target_name>",
    "value": "<content>"
  }
}
```

**Client interaction**: Run client, type `receiver:message` format to send (e.g., `Bob:Hello!`), type `quit` to exit.
