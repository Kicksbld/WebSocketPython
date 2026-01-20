"""
Widget de connexion.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ..styles import COLORS, FONT_FAMILY


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
