"""
Interface principale du chat.
"""
import base64
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QFileDialog, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ..styles import COLORS, FONT_FAMILY
from .message_bubble import MessageBubble
from .media_panel import MediaPanel


class ChatWidget(QWidget):
    """Interface principale du chat."""
    disconnect_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.username = ""
        self.connection_info = ""
        self.send_callback = None
        self.send_image_callback = None
        self.send_audio_callback = None
        self.send_video_callback = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg_dark']};")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        main_layout.addWidget(self._create_header())

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

        # Content Area
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        content_layout.addWidget(self._create_chat_area(), stretch=3)

        self.media_panel = MediaPanel()
        content_layout.addWidget(self.media_panel)

        main_layout.addLayout(content_layout, stretch=1)

        # Input Bar
        main_layout.addWidget(self._create_input_bar())

    def _create_header(self):
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
        status_dot = QLabel("*")
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

        return header

    def _create_chat_area(self):
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

        return chat_area

    def _create_input_bar(self):
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
        self.attach_btn = QPushButton("+")
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
        self.send_btn = QPushButton("SEND")
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

        return bottom_bar

    def set_connection_info(self, username, ip, port):
        self.username = username
        self.connection_info = f"{ip}:{port}"
        self.connection_label.setText(f"Connected as {username} - {self.connection_info}")
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
        elif msg_type == "video":
            self.media_panel.show_video(content)

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
            "Images (*.png *.jpg *.jpeg *.gif *.bmp);;Audio (*.mp3 *.wav *.ogg *.m4a);;Video (*.mp4 *.avi *.mov *.mkv *.webm);;All Files (*)"
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
        elif ext in ['mp4', 'avi', 'mov', 'mkv', 'webm']:
            if self.send_video_callback:
                self.send_video_callback(file_path, receiver)
                with open(file_path, 'rb') as f:
                    video_data = "VIDEO:" + base64.b64encode(f.read()).decode('utf-8')
                self.add_message(self.username, receiver, video_data, "video")

    def clear_messages(self):
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
