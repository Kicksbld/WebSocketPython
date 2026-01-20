import sys
import base64
import tempfile
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea,
    QStackedWidget, QFrame, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QUrl
from PyQt5.QtGui import QPixmap, QFont, QIcon
from PyQt5.QtMultimedia import QMediaPlayer, QAudioOutput

from Context import Context
from Message import Message, MessageType
from WSClient import WSClient


class QtWSClient(QThread):
    """Qt wrapper around WSClient - runs the client in a separate thread with Qt signals."""
    message_received = pyqtSignal(object)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)

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
        import websocket
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

        # Emit signal for UI
        self.message_received.emit(received_msg)

        # Send ack for RECEPTION messages (same as WSClient)
        if received_msg.message_type in [MessageType.RECEPTION.TEXT, MessageType.RECEPTION.IMAGE, MessageType.RECEPTION.AUDIO]:
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

    def disconnect(self):
        """Disconnect - same logic as WSClient input_loop disconnect."""
        if self.client and self.client.ws:
            disconnect_msg = Message(MessageType.SYS_MESSAGE, emitter=self.username, receiver="", value="Disconnect")
            self.client.ws.send(disconnect_msg.to_json())
            self.client.ws.close()


class LoginWidget(QWidget):
    """Vue de connexion."""
    connect_requested = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #f0f0f0;")

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedWidth(400)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                padding: 30px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        title = QLabel("Global Chat System")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #1a1a2e;")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        card_layout.addSpacing(10)

        name_label = QLabel("Name")
        name_label.setStyleSheet("color: #1a1a2e; font-size: 12px; font-weight: bold;")
        card_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")
        self.name_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4169E1;
            }
        """)
        card_layout.addWidget(self.name_input)

        ip_label = QLabel("IP Address")
        ip_label.setStyleSheet("color: #1a1a2e; font-size: 12px; font-weight: bold;")
        card_layout.addWidget(ip_label)

        self.ip_input = QLineEdit()
        self.ip_input.setText("192.168.4.230")
        self.ip_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4169E1;
            }
        """)
        card_layout.addWidget(self.ip_input)

        port_label = QLabel("Port")
        port_label.setStyleSheet("color: #1a1a2e; font-size: 12px; font-weight: bold;")
        card_layout.addWidget(port_label)

        self.port_input = QLineEdit()
        self.port_input.setText("9000")
        self.port_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #4169E1;
            }
        """)
        card_layout.addWidget(self.port_input)

        card_layout.addSpacing(10)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3458c9;
            }
            QPushButton:pressed {
                background-color: #2a4aa8;
            }
        """)
        self.connect_btn.clicked.connect(self.on_connect)
        card_layout.addWidget(self.connect_btn)

        main_layout.addWidget(card)

    def on_connect(self):
        name = self.name_input.text().strip()
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()

        if name and ip and port:
            self.connect_requested.emit(name, ip, port)


class MessageBubble(QFrame):
    """Widget pour afficher un message."""

    def __init__(self, sender, receiver, content, timestamp, msg_type="text"):
        super().__init__()
        self.init_ui(sender, receiver, content, timestamp, msg_type)

    def init_ui(self, sender, receiver, content, timestamp, msg_type):
        self.setStyleSheet("""
            QFrame {
                background-color: transparent;
                margin: 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        header = QLabel(f"<b>{sender}</b> <span style='color: gray;'>→</span> {receiver}  <span style='color: #888; font-size: 10px;'>{timestamp}</span>")
        header.setStyleSheet("color: #333; font-size: 11px;")
        layout.addWidget(header)

        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(10, 10, 10, 10)

        if msg_type == "text":
            content_label = QLabel(content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("color: #1a1a2e; font-size: 13px;")
            content_layout.addWidget(content_label)
        elif msg_type == "image":
            content_label = QLabel("[Image]")
            content_label.setStyleSheet("color: #4169E1; font-size: 13px;")
            content_layout.addWidget(content_label)
        elif msg_type == "audio":
            content_label = QLabel("[Audio]")
            content_label.setStyleSheet("color: #4169E1; font-size: 13px;")
            content_layout.addWidget(content_label)

        layout.addWidget(content_frame)


class MediaPanel(QWidget):
    """Panneau pour afficher le dernier media partage."""

    def __init__(self):
        super().__init__()
        self.media_player = None
        self.audio_output = None
        self.temp_audio_file = None
        self.is_playing = False
        self.init_ui()

    def init_ui(self):
        self.setFixedWidth(280)
        self.setStyleSheet("background-color: white; border-left: 1px solid #e0e0e0;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("Media Panel")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setStyleSheet("color: #1a1a2e;")
        layout.addWidget(title)

        subtitle = QLabel("Latest shared media")
        subtitle.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setAlignment(Qt.AlignCenter)

        self.placeholder = QWidget()
        placeholder_layout = QVBoxLayout(self.placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border-radius: 40px;
                padding: 20px;
            }
        """)
        icon_label.setFixedSize(80, 80)
        icon_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(icon_label, alignment=Qt.AlignCenter)

        no_media_label = QLabel("No media shared yet")
        no_media_label.setStyleSheet("color: #888; font-size: 12px;")
        no_media_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(no_media_label)

        self.content_layout.addWidget(self.placeholder)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.hide()
        self.content_layout.addWidget(self.image_label)

        self.audio_widget = QWidget()
        audio_layout = QVBoxLayout(self.audio_widget)
        audio_layout.setAlignment(Qt.AlignCenter)

        self.play_pause_btn = QPushButton("Play")
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 15px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3458c9;
            }
        """)
        self.play_pause_btn.clicked.connect(self.toggle_audio)
        audio_layout.addWidget(self.play_pause_btn, alignment=Qt.AlignCenter)

        self.audio_widget.hide()
        self.content_layout.addWidget(self.audio_widget)

        layout.addWidget(self.content_area)
        layout.addStretch()

    def show_image(self, base64_data):
        self.placeholder.hide()
        self.audio_widget.hide()
        self.image_label.show()

        if base64_data.startswith("IMG:"):
            base64_data = base64_data[4:]

        image_data = base64.b64decode(base64_data)
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        scaled = pixmap.scaledToWidth(250, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)

    def show_audio(self, base64_data):
        self.placeholder.hide()
        self.image_label.hide()
        self.audio_widget.show()

        if base64_data.startswith("AUDIO:"):
            base64_data = base64_data[6:]

        audio_bytes = base64.b64decode(base64_data)

        if self.temp_audio_file:
            try:
                os.remove(self.temp_audio_file)
            except:
                pass

        fd, self.temp_audio_file = tempfile.mkstemp(suffix=".mp3")
        with os.fdopen(fd, 'wb') as f:
            f.write(audio_bytes)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setSource(QUrl.fromLocalFile(self.temp_audio_file))

        self.is_playing = False
        self.play_pause_btn.setText("Play")

    def toggle_audio(self):
        if not self.media_player:
            return

        if self.is_playing:
            self.media_player.pause()
            self.play_pause_btn.setText("Play")
        else:
            self.media_player.play()
            self.play_pause_btn.setText("Pause")

        self.is_playing = not self.is_playing


class ChatWidget(QWidget):
    """Interface principale du chat."""
    disconnect_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.username = ""
        self.connection_info = ""
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #f8f8f8;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
                padding: 15px;
            }
        """)
        header_layout = QHBoxLayout(header)

        title_area = QVBoxLayout()
        title = QLabel("Global Chat System")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #1a1a2e;")
        title_area.addWidget(title)

        self.connection_label = QLabel("Connected as ...")
        self.connection_label.setStyleSheet("color: #666; font-size: 11px;")
        title_area.addWidget(self.connection_label)

        header_layout.addLayout(title_area)
        header_layout.addStretch()

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #DC143C;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #b8102f;
            }
        """)
        self.disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        header_layout.addWidget(self.disconnect_btn)

        main_layout.addWidget(header)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        chat_area = QWidget()
        chat_area.setStyleSheet("background-color: white;")
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
        """)

        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.setSpacing(5)

        self.scroll_area.setWidget(self.messages_widget)
        chat_layout.addWidget(self.scroll_area)

        content_layout.addWidget(chat_area, stretch=3)

        self.media_panel = MediaPanel()
        content_layout.addWidget(self.media_panel)

        main_layout.addLayout(content_layout, stretch=1)

        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("""
            QFrame {
                background-color: white;
                border-top: 1px solid #e0e0e0;
                padding: 10px;
            }
        """)
        bottom_layout = QHBoxLayout(bottom_bar)

        send_to_label = QLabel("Send to:")
        send_to_label.setStyleSheet("color: #666; font-size: 11px;")
        bottom_layout.addWidget(send_to_label)

        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("Recipient name")
        self.recipient_input.setFixedWidth(120)
        self.recipient_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4169E1;
            }
        """)
        bottom_layout.addWidget(self.recipient_input)

        message_label = QLabel("Message:")
        message_label.setStyleSheet("color: #666; font-size: 11px;")
        bottom_layout.addWidget(message_label)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #4169E1;
            }
        """)
        self.message_input.returnPressed.connect(self.on_send)
        bottom_layout.addWidget(self.message_input, stretch=1)

        self.attach_btn = QPushButton("Attach")
        self.attach_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px 15px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        self.attach_btn.clicked.connect(self.on_attach)
        bottom_layout.addWidget(self.attach_btn)

        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4169E1;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3458c9;
            }
            QPushButton:disabled {
                background-color: #a0a0a0;
            }
        """)
        self.send_btn.clicked.connect(self.on_send)
        bottom_layout.addWidget(self.send_btn)

        main_layout.addWidget(bottom_bar)

        self.send_callback = None
        self.send_image_callback = None
        self.send_audio_callback = None

    def set_connection_info(self, username, ip, port):
        self.username = username
        self.connection_info = f"{ip}:{port}"
        self.connection_label.setText(f"Connected as {username} ({self.connection_info})")

    def add_message(self, sender, receiver, content, msg_type="text"):
        timestamp = datetime.now().strftime("%H:%M")
        bubble = MessageBubble(sender, receiver, content, timestamp, msg_type)
        self.messages_layout.addWidget(bubble)

        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

        if msg_type == "image":
            self.media_panel.show_image(content)
        elif msg_type == "audio":
            self.media_panel.show_audio(content)

    def on_send(self):
        if not self.send_callback:
            return

        receiver = self.recipient_input.text().strip()
        content = self.message_input.text().strip()

        if receiver and content:
            self.send_callback(content, receiver)
            self.add_message(self.username, receiver, content, "text")
            self.message_input.clear()

    def on_attach(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select media file",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp);;Audio (*.mp3 *.wav *.ogg *.m4a);;All Files (*)"
        )

        if not file_path:
            return

        receiver = self.recipient_input.text().strip()
        if not receiver:
            return

        ext = file_path.lower().split('.')[-1]

        if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
            if self.send_image_callback:
                self.send_image_callback(file_path, receiver)
                with open(file_path, 'rb') as f:
                    img_data = "IMG:" + base64.b64encode(f.read()).decode('utf-8')
                self.add_message(self.username, receiver, img_data, "image")
        elif ext in ['mp3', 'wav', 'ogg', 'm4a']:
            if self.send_audio_callback:
                self.send_audio_callback(file_path, receiver)
                with open(file_path, 'rb') as f:
                    audio_data = "AUDIO:" + base64.b64encode(f.read()).decode('utf-8')
                self.add_message(self.username, receiver, audio_data, "audio")

    def clear_messages(self):
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class ChatApp(QMainWindow):
    """Application principale."""

    def __init__(self):
        super().__init__()
        self.ws_thread = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Global Chat System")
        self.setMinimumSize(1000, 700)

        self.stack = QStackedWidget()
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

        self.chat_widget.send_callback = self.send_text
        self.chat_widget.send_image_callback = self.send_image
        self.chat_widget.send_audio_callback = self.send_audio

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec())
