"""
Client WebSocket Qt - Wrapper autour de WSClient avec signaux Qt.
"""
import websocket
from PyQt5.QtCore import QThread, pyqtSignal

from Context import Context
from Message import Message, MessageType
from WSClient import WSClient


class QtWSClient(QThread):
    """Qt wrapper around WSClient - runs the client in a separate thread with Qt signals."""
    message_received = pyqtSignal(object)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)
    clients_updated = pyqtSignal(list)

    def __init__(self, host, port, username):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.client = None

    def run(self):
        """Create and run WSClient with overridden callbacks."""
        ctx = Context(self.host, self.port)
        self.client = WSClient(ctx, self.username)

        # Override WSClient callbacks to emit Qt signals
        self.client.on_open = self._on_open
        self.client.on_message = self._on_message
        self.client.on_error = self._on_error
        self.client.on_close = self._on_close

        # Rebuild WebSocketApp with new callbacks
        self.client.ws = websocket.WebSocketApp(
            ctx.url(),
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        self.client.ws.run_forever()

    def _on_open(self, ws):
        """Called when connection opens - reuses WSClient's declaration logic."""
        self.client.connected = True
        self.connected.emit()
        # Send declaration (same as WSClient.on_open)
        message = Message(MessageType.DECLARATION, emitter=self.username, receiver="", value="")
        ws.send(message.to_json())

    def _on_message(self, ws, message):
        """Called on message - reuses WSClient's ping/pong and ack logic."""
        received_msg = Message.from_json(message)

        # Handle ping (same as WSClient)
        if received_msg.message_type == MessageType.SYS_MESSAGE and received_msg.value == "ping":
            pong_msg = Message(MessageType.SYS_MESSAGE, emitter=self.username, receiver="", value="pong")
            ws.send(pong_msg.to_json())
            return

        # Handle client list update
        if received_msg.message_type == MessageType.RECEPTION.CLIENT_LIST:
            clients = [c for c in received_msg.value if c != self.username]
            self.clients_updated.emit(clients)
            return

        # Emit signal for UI
        self.message_received.emit(received_msg)

        # Send ack for RECEPTION messages (same as WSClient)
        if received_msg.message_type in [MessageType.RECEPTION.TEXT, MessageType.RECEPTION.IMAGE, MessageType.RECEPTION.AUDIO, MessageType.RECEPTION.VIDEO]:
            ack_msg = Message(MessageType.SYS_MESSAGE, emitter=self.username, receiver="", value="MESSAGE OK")
            ws.send(ack_msg.to_json())

    def _on_error(self, ws, error):
        self.error.emit(str(error))

    def _on_close(self, ws, close_status_code, close_msg):
        self.client.connected = False
        self.disconnected.emit()

    def send_text(self, value, dest):
        """Reuse WSClient.send()"""
        if self.client and self.client.ws:
            self.client.send(value, dest)

    def send_image(self, filepath, dest):
        """Reuse WSClient.send_image()"""
        if self.client and self.client.ws:
            self.client.send_image(filepath, dest)

    def send_audio(self, filepath, dest):
        """Reuse WSClient.send_audio()"""
        if self.client and self.client.ws:
            self.client.send_audio(filepath, dest)

    def send_video(self, filepath, dest):
        """Reuse WSClient.send_video()"""
        if self.client and self.client.ws:
            self.client.send_video(filepath, dest)

    def disconnect(self):
        """Disconnect - same logic as WSClient input_loop disconnect."""
        if self.client and self.client.ws:
            disconnect_msg = Message(MessageType.SYS_MESSAGE, emitter=self.username, receiver="", value="Disconnect")
            self.client.ws.send(disconnect_msg.to_json())
            self.client.ws.close()
