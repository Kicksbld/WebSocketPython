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


# ═══════════════════════════════════════════════════════════════════════════════
# DARK LUXE GLASSMORPHISM - Color System
# ═══════════════════════════════════════════════════════════════════════════════

COLORS = {
    # Base colors
    "bg_dark": "#0d0d12",
    "bg_surface": "#1a1a24",
    "bg_glass": "rgba(30, 30, 45, 0.85)",
    "bg_glass_light": "rgba(40, 40, 55, 0.9)",

    # Borders
    "border_subtle": "rgba(255, 255, 255, 0.08)",
    "border_glow": "rgba(0, 245, 212, 0.3)",

    # Accent colors
    "primary": "#00f5d4",        # Electric cyan
    "secondary": "#f72585",      # Magenta
    "accent_purple": "#7b2ff7",  # Purple for gradients

    # Text colors
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0b0",
    "text_muted": "#606070",

    # Status colors
    "success": "#00f5d4",
    "error": "#ff4757",
    "warning": "#ffa502",
}

# Cross-platform font selection
import platform
if platform.system() == "Darwin":
    FONT_FAMILY = ".AppleSystemUIFont"  # macOS system font
else:
    FONT_FAMILY = "Segoe UI"  # Windows system font

# Global stylesheet for the entire application
GLOBAL_STYLE = f"""
    QMainWindow {{
        background-color: {COLORS['bg_dark']};
    }}
    QWidget {{
        font-family: '{FONT_FAMILY}';
    }}
    QScrollBar:vertical {{
        background: {COLORS['bg_surface']};
        width: 8px;
        border-radius: 4px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['text_muted']};
        border-radius: 4px;
        min-height: 40px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS['primary']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
"""


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
        self.setStyleSheet(f"background-color: {COLORS['bg_dark']};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Glass card container - full window
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_glass']};
                border: none;
                border-radius: 0px;
                padding: 60px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(18)
        card_layout.setAlignment(Qt.AlignCenter)

        # Inner container for form with max width
        form_container = QWidget()
        form_container.setFixedWidth(380)
        form_container.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(18)
        form_layout.setContentsMargins(0, 0, 0, 0)

        # Decorative accent line
        accent_line = QFrame()
        accent_line.setFixedHeight(3)
        accent_line.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['secondary']});
                border-radius: 2px;
                border: none;
            }}
        """)
        form_layout.addWidget(accent_line)

        form_layout.addSpacing(10)

        # Title with glow effect
        title = QLabel("GLOBAL CHAT")
        title.setFont(QFont(FONT_FAMILY, 24, QFont.Bold))
        title.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            letter-spacing: 4px;
        """)
        title.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Secure • Fast • Connected")
        subtitle.setFont(QFont(FONT_FAMILY, 10))
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; letter-spacing: 2px;")
        subtitle.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(subtitle)

        form_layout.addSpacing(25)

        # Input styling
        input_style = f"""
            QLineEdit {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 14px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['primary']};
                background-color: {COLORS['bg_glass_light']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_muted']};
            }}
        """

        label_style = f"color: {COLORS['text_secondary']}; font-size: 11px; font-weight: bold; letter-spacing: 1px;"

        # Name input
        name_label = QLabel("USERNAME")
        name_label.setStyleSheet(label_style)
        form_layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your username")
        self.name_input.setStyleSheet(input_style)
        form_layout.addWidget(self.name_input)

        # IP input
        ip_label = QLabel("SERVER ADDRESS")
        ip_label.setStyleSheet(label_style)
        form_layout.addWidget(ip_label)

        self.ip_input = QLineEdit()
        self.ip_input.setText("192.168.4.230")
        self.ip_input.setStyleSheet(input_style)
        form_layout.addWidget(self.ip_input)

        # Port input
        port_label = QLabel("PORT")
        port_label.setStyleSheet(label_style)
        form_layout.addWidget(port_label)

        self.port_input = QLineEdit()
        self.port_input.setText("9000")
        self.port_input.setStyleSheet(input_style)
        form_layout.addWidget(self.port_input)

        form_layout.addSpacing(20)

        # Connect button with gradient
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        self.connect_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['accent_purple']});
                color: {COLORS['bg_dark']};
                border: none;
                border-radius: 12px;
                padding: 16px;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_purple']}, stop:1 {COLORS['secondary']});
            }}
            QPushButton:pressed {{
                background: {COLORS['secondary']};
            }}
        """)
        self.connect_btn.clicked.connect(self.on_connect)
        form_layout.addWidget(self.connect_btn)

        card_layout.addWidget(form_container)

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
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                margin: 4px 0;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(6)

        # Header with sender info
        header = QLabel(f"<span style='color: {COLORS['primary']}; font-weight: bold;'>{sender}</span> "
                       f"<span style='color: {COLORS['text_muted']};'>→</span> "
                       f"<span style='color: {COLORS['text_secondary']};'>{receiver}</span>  "
                       f"<span style='color: {COLORS['text_muted']}; font-size: 10px;'>{timestamp}</span>")
        header.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;")
        layout.addWidget(header)

        # Content frame with glass effect
        content_frame = QFrame()
        content_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_glass']};
                border: 1px solid {COLORS['border_subtle']};
                border-left: 3px solid {COLORS['primary']};
                border-radius: 12px;
                padding: 12px;
            }}
        """)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(14, 12, 14, 12)

        if msg_type == "text":
            content_label = QLabel(content)
            content_label.setWordWrap(True)
            content_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; background: transparent; line-height: 1.4;")
            content_layout.addWidget(content_label)
        elif msg_type == "image":
            content_label = QLabel("📷  Image attached")
            content_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: 13px; background: transparent;")
            content_layout.addWidget(content_label)
        elif msg_type == "audio":
            content_label = QLabel("🎵  Audio message")
            content_label.setStyleSheet(f"color: {COLORS['secondary']}; font-size: 13px; background: transparent;")
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
        self.setFixedWidth(300)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_surface']};
                border-left: 1px solid {COLORS['border_subtle']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 25, 20, 20)

        # Header section
        header_frame = QFrame()
        header_frame.setStyleSheet("background: transparent; border: none;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)

        title = QLabel("MEDIA PANEL")
        title.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; letter-spacing: 2px; background: transparent;")
        header_layout.addWidget(title)

        subtitle = QLabel("Latest shared media")
        subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        header_layout.addWidget(subtitle)

        layout.addWidget(header_frame)

        # Decorative line
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {COLORS['border_subtle']}; border: none;")
        layout.addWidget(line)

        layout.addSpacing(25)

        self.content_area = QWidget()
        self.content_area.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setAlignment(Qt.AlignCenter)

        # Placeholder when no media
        self.placeholder = QWidget()
        self.placeholder.setStyleSheet("background: transparent;")
        placeholder_layout = QVBoxLayout(self.placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        placeholder_layout.setSpacing(15)

        icon_label = QLabel("📁")
        icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_glass']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 40px;
                padding: 20px;
                font-size: 28px;
            }}
        """)
        icon_label.setFixedSize(80, 80)
        icon_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(icon_label, alignment=Qt.AlignCenter)

        no_media_label = QLabel("No media shared yet")
        no_media_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; background: transparent;")
        no_media_label.setAlignment(Qt.AlignCenter)
        placeholder_layout.addWidget(no_media_label)

        self.content_layout.addWidget(self.placeholder)

        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border: 2px solid {COLORS['border_subtle']};
                border-radius: 12px;
                padding: 4px;
            }}
        """)
        self.image_label.hide()
        self.content_layout.addWidget(self.image_label)

        # Audio player widget
        self.audio_widget = QWidget()
        self.audio_widget.setStyleSheet("background: transparent;")
        audio_layout = QVBoxLayout(self.audio_widget)
        audio_layout.setAlignment(Qt.AlignCenter)
        audio_layout.setSpacing(15)

        audio_icon = QLabel("🎵")
        audio_icon.setStyleSheet("font-size: 48px; background: transparent;")
        audio_icon.setAlignment(Qt.AlignCenter)
        audio_layout.addWidget(audio_icon, alignment=Qt.AlignCenter)

        self.play_pause_btn = QPushButton("▶  PLAY")
        self.play_pause_btn.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.play_pause_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['accent_purple']});
                color: {COLORS['bg_dark']};
                border: none;
                border-radius: 25px;
                padding: 15px 35px;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_purple']}, stop:1 {COLORS['secondary']});
            }}
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
        self.play_pause_btn.setText("▶  PLAY")

    def toggle_audio(self):
        if not self.media_player:
            return

        if self.is_playing:
            self.media_player.pause()
            self.play_pause_btn.setText("▶  PLAY")
        else:
            self.media_player.play()
            self.play_pause_btn.setText("⏸  PAUSE")

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
        self.setStyleSheet(f"background-color: {COLORS['bg_dark']};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ═══════════════════════════════════════════════════════════════════
        # HEADER
        # ═══════════════════════════════════════════════════════════════════
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_surface']};
                border-bottom: 1px solid {COLORS['border_subtle']};
                padding: 18px 25px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Title area
        title_area = QVBoxLayout()
        title_area.setSpacing(4)

        title = QLabel("GLOBAL CHAT")
        title.setFont(QFont(FONT_FAMILY, 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; letter-spacing: 3px; background: transparent;")
        title_area.addWidget(title)

        self.connection_label = QLabel("Connecting...")
        self.connection_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        title_area.addWidget(self.connection_label)

        header_layout.addLayout(title_area)
        header_layout.addStretch()

        # Status indicator
        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"color: {COLORS['primary']}; font-size: 10px; background: transparent;")
        header_layout.addWidget(status_dot)

        status_label = QLabel("Online")
        status_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: 11px; margin-right: 20px; background: transparent;")
        header_layout.addWidget(status_label)

        # Disconnect button
        self.disconnect_btn = QPushButton("DISCONNECT")
        self.disconnect_btn.setFont(QFont(FONT_FAMILY, 10, QFont.Bold))
        self.disconnect_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['error']};
                border: 1px solid {COLORS['error']};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: {COLORS['text_primary']};
            }}
        """)
        self.disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        header_layout.addWidget(self.disconnect_btn)

        main_layout.addWidget(header)

        # Accent glow line under header
        accent_line = QFrame()
        accent_line.setFixedHeight(2)
        accent_line.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:0.5 {COLORS['accent_purple']}, stop:1 {COLORS['secondary']});
                border: none;
            }}
        """)
        main_layout.addWidget(accent_line)

        # ═══════════════════════════════════════════════════════════════════
        # CONTENT AREA
        # ═══════════════════════════════════════════════════════════════════
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Chat area
        chat_area = QWidget()
        chat_area.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {COLORS['bg_dark']};
            }}
        """)

        self.messages_widget = QWidget()
        self.messages_widget.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setContentsMargins(15, 15, 15, 15)
        self.messages_layout.setSpacing(8)

        self.scroll_area.setWidget(self.messages_widget)
        chat_layout.addWidget(self.scroll_area)

        content_layout.addWidget(chat_area, stretch=3)

        self.media_panel = MediaPanel()
        content_layout.addWidget(self.media_panel)

        main_layout.addLayout(content_layout, stretch=1)

        # ═══════════════════════════════════════════════════════════════════
        # INPUT BAR
        # ═══════════════════════════════════════════════════════════════════
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_surface']};
                border-top: 1px solid {COLORS['border_subtle']};
                padding: 15px 20px;
            }}
        """)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setSpacing(12)

        # Input field styling
        input_style = f"""
            QLineEdit {{
                background-color: {COLORS['bg_dark']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 13px;
                color: {COLORS['text_primary']};
            }}
            QLineEdit:focus {{
                border: 1px solid {COLORS['primary']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_muted']};
            }}
        """

        label_style = f"color: {COLORS['text_muted']}; font-size: 10px; font-weight: bold; letter-spacing: 1px; background: transparent;"

        # Recipient input
        recipient_container = QVBoxLayout()
        recipient_container.setSpacing(4)
        send_to_label = QLabel("TO")
        send_to_label.setStyleSheet(label_style)
        recipient_container.addWidget(send_to_label)

        self.recipient_input = QLineEdit()
        self.recipient_input.setPlaceholderText("Recipient")
        self.recipient_input.setFixedWidth(130)
        self.recipient_input.setStyleSheet(input_style)
        recipient_container.addWidget(self.recipient_input)
        bottom_layout.addLayout(recipient_container)

        # Message input
        message_container = QVBoxLayout()
        message_container.setSpacing(4)
        message_label = QLabel("MESSAGE")
        message_label.setStyleSheet(label_style)
        message_container.addWidget(message_label)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.setStyleSheet(input_style)
        self.message_input.returnPressed.connect(self.on_send)
        message_container.addWidget(self.message_input)
        bottom_layout.addLayout(message_container, stretch=1)

        # Button container
        button_container = QVBoxLayout()
        button_container.setSpacing(4)
        button_spacer = QLabel("")
        button_spacer.setStyleSheet("background: transparent;")
        button_container.addWidget(button_spacer)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        # Attach button
        self.attach_btn = QPushButton("📎")
        self.attach_btn.setFixedSize(44, 44)
        self.attach_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_glass']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 10px;
                font-size: 18px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_glass_light']};
                border-color: {COLORS['primary']};
                color: {COLORS['primary']};
            }}
        """)
        self.attach_btn.clicked.connect(self.on_attach)
        button_row.addWidget(self.attach_btn)

        # Send button
        self.send_btn = QPushButton("SEND  →")
        self.send_btn.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 {COLORS['accent_purple']});
                color: {COLORS['bg_dark']};
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['accent_purple']}, stop:1 {COLORS['secondary']});
            }}
            QPushButton:disabled {{
                background: {COLORS['text_muted']};
            }}
        """)
        self.send_btn.clicked.connect(self.on_send)
        button_row.addWidget(self.send_btn)

        button_container.addLayout(button_row)
        bottom_layout.addLayout(button_container)

        main_layout.addWidget(bottom_bar)

        self.send_callback = None
        self.send_image_callback = None
        self.send_audio_callback = None

    def set_connection_info(self, username, ip, port):
        self.username = username
        self.connection_info = f"{ip}:{port}"
        self.connection_label.setText(f"Connected as {username} • {self.connection_info}")
        self.connection_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; background: transparent;")

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
