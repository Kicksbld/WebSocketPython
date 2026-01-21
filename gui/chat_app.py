"""
Application principale de chat.
"""
from PyQt5.QtWidgets import QMainWindow, QStackedWidget

from Message import MessageType
from .styles import COLORS, GLOBAL_STYLE
from .qt_ws_client import QtWSClient
from .widgets import LoginWidget, ChatWidget


class ChatApp(QMainWindow):
    """Application principale."""

    def __init__(self):
        super().__init__()
        self.ws_thread = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("GLOBAL CHAT")
        self.setMinimumSize(1100, 750)

        # Apply global dark theme stylesheet
        self.setStyleSheet(GLOBAL_STYLE)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        self.setCentralWidget(self.stack)

        self.login_widget = LoginWidget()
        self.login_widget.connect_requested.connect(self.on_connect)
        self.stack.addWidget(self.login_widget)

        self.chat_widget = ChatWidget()
        self.chat_widget.disconnect_requested.connect(self.on_disconnect)
        self.stack.addWidget(self.chat_widget)

        self.stack.setCurrentIndex(0)

    def on_connect(self, name, ip, port):
        self.ws_thread = QtWSClient(ip, port, name)
        self.ws_thread.connected.connect(lambda: self.on_connected(name, ip, port))
        self.ws_thread.disconnected.connect(self.on_disconnected)
        self.ws_thread.message_received.connect(self.on_message)
        self.ws_thread.error.connect(self.on_error)
        self.ws_thread.clients_updated.connect(self.chat_widget.update_clients_list)

        self.chat_widget.send_callback = self.send_text
        self.chat_widget.send_image_callback = self.send_image
        self.chat_widget.send_audio_callback = self.send_audio
        self.chat_widget.send_video_callback = self.send_video

        self.ws_thread.start()

    def on_connected(self, name, ip, port):
        self.chat_widget.set_connection_info(name, ip, port)
        self.chat_widget.clear_messages()
        self.stack.setCurrentIndex(1)

    def on_disconnected(self):
        self.stack.setCurrentIndex(0)
        if self.ws_thread:
            self.ws_thread.quit()
            self.ws_thread.wait()
            self.ws_thread = None

    def on_disconnect(self):
        if self.ws_thread:
            self.ws_thread.disconnect()

    def on_message(self, msg):
        if msg.message_type in [MessageType.RECEPTION.TEXT]:
            self.chat_widget.add_message(msg.emitter, msg.receiver, msg.value, "text")
        elif msg.message_type in [MessageType.RECEPTION.IMAGE]:
            self.chat_widget.add_message(msg.emitter, msg.receiver, msg.value, "image")
        elif msg.message_type in [MessageType.RECEPTION.AUDIO]:
            self.chat_widget.add_message(msg.emitter, msg.receiver, msg.value, "audio")
        elif msg.message_type in [MessageType.RECEPTION.VIDEO]:
            self.chat_widget.add_message(msg.emitter, msg.receiver, msg.value, "video")
        elif msg.message_type == MessageType.SYS_MESSAGE:
            pass
        elif msg.message_type == MessageType.WARNING:
            self.chat_widget.add_message("SYSTEM", self.ws_thread.username, msg.value, "text")

    def on_error(self, error_msg):
        self.chat_widget.add_message("SYSTEM", "", f"Error: {error_msg}", "text")

    def send_text(self, content, receiver):
        """Reuse WSClient.send() via QtWSClient"""
        if self.ws_thread:
            self.ws_thread.send_text(content, receiver)

    def send_image(self, filepath, receiver):
        """Reuse WSClient.send_image() via QtWSClient"""
        if self.ws_thread:
            self.ws_thread.send_image(filepath, receiver)

    def send_audio(self, filepath, receiver):
        """Reuse WSClient.send_audio() via QtWSClient"""
        if self.ws_thread:
            self.ws_thread.send_audio(filepath, receiver)

    def send_video(self, filepath, receiver):
        """Reuse WSClient.send_video() via QtWSClient"""
        if self.ws_thread:
            self.ws_thread.send_video(filepath, receiver)
