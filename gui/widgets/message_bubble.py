"""
Widget bulle de message.
"""
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel

from ..styles import COLORS


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
            content_label = QLabel("Image attached")
            content_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: 13px; background: transparent;")
            content_layout.addWidget(content_label)
        elif msg_type == "audio":
            content_label = QLabel("Audio message")
            content_label.setStyleSheet(f"color: {COLORS['secondary']}; font-size: 13px; background: transparent;")
            content_layout.addWidget(content_label)
        elif msg_type == "video":
            content_label = QLabel("Video attached")
            content_label.setStyleSheet(f"color: {COLORS['accent_purple']}; font-size: 13px; background: transparent;")
            content_layout.addWidget(content_label)

        layout.addWidget(content_frame)
