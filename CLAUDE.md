# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python WebSocket messaging system with both CLI and PyQt5 GUI clients. Supports text, image, audio, and video messaging between named clients through a central server.

## Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install websocket-server websocket-client PyQt5 flask

# Run server (dev mode - localhost:8000)
python WSServer.py

# Run CLI client
python WSClient.py <username>

# Run GUI client
python ChatGUI.py

# Run Admin Dashboard (Flask - http://127.0.0.1:5000)
python admin/app.py
```

## Architecture

**Three client interfaces**:
- `WSClient.py`: CLI client with interactive recipient selection menu
- `ChatGUI.py`: PyQt5 GUI application using `QtWSClient` wrapper that runs WSClient in a QThread with Qt signals
- `admin/app.py`: Flask web admin dashboard with real-time WebSocket monitoring

**Message routing**: Server maintains `clients` dict mapping usernames to WebSocket connections. Clients register via `DECLARATION`, then route messages through `ENVOI.*` types. Server converts to `RECEPTION.*` for delivery. Use receiver `"ALL"` for broadcast.

**Message types** (in `Message.py`):
- `DECLARATION`: Client registration
- `ENVOI.{TEXT,IMAGE,AUDIO,VIDEO}`: Outgoing messages
- `RECEPTION.{TEXT,IMAGE,AUDIO,VIDEO,CLIENT_LIST}`: Incoming messages
- `SYS_MESSAGE`: System messages (ping/pong, acks, disconnect)

**Media encoding**: Images/audio/video sent as base64 with prefix (`IMG:`, `AUDIO:`, `VIDEO:`)

**Context configuration**: `Context.dev()` = localhost:8000, `Context.prod()` = 192.168.4.230:9000

**GUI structure** (`gui/`):
- `chat_app.py`: Main QMainWindow with login/chat widget stack
- `qt_ws_client.py`: QThread wrapper emitting pyqtSignals for UI updates
- `styles.py`: Dark theme colors and stylesheets

**Admin Dashboard** (`admin/`):
- `app.py`: Flask application serving the dashboard
- `templates/index.html`: Dashboard HTML template
- `static/css/style.css`: Dark theme styles
- `static/js/app.js`: JavaScript WebSocket client for admin monitoring
