"""
Panneau pour afficher le dernier media partage.
"""
import base64
import tempfile
import os

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from ..styles import COLORS, FONT_FAMILY


class MediaPanel(QWidget):
    """Panneau pour afficher le dernier media partage."""

    def __init__(self):
        super().__init__()
        self.media_player = None
        self.temp_audio_file = None
        self.temp_video_file = None
        self.is_playing = False
        self.current_media_type = None  # "audio" or "video"
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

        icon_label = QLabel("No media")
        icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS['bg_glass']};
                border: 1px solid {COLORS['border_subtle']};
                border-radius: 40px;
                padding: 20px;
                font-size: 14px;
                color: {COLORS['text_muted']};
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

        audio_icon = QLabel("Audio")
        audio_icon.setStyleSheet(f"font-size: 24px; background: transparent; color: {COLORS['text_secondary']};")
        audio_icon.setAlignment(Qt.AlignCenter)
        audio_layout.addWidget(audio_icon, alignment=Qt.AlignCenter)

        self.play_pause_btn = QPushButton("PLAY")
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

        # Video player widget
        self.video_widget = QWidget()
        self.video_widget.setStyleSheet("background: transparent;")
        video_layout = QVBoxLayout(self.video_widget)
        video_layout.setAlignment(Qt.AlignCenter)
        video_layout.setSpacing(15)

        self.video_display = QVideoWidget()
        self.video_display.setFixedSize(250, 180)
        self.video_display.setStyleSheet(f"""
            QVideoWidget {{
                background-color: {COLORS['bg_dark']};
                border: 2px solid {COLORS['border_subtle']};
                border-radius: 12px;
            }}
        """)
        video_layout.addWidget(self.video_display, alignment=Qt.AlignCenter)

        self.video_play_btn = QPushButton("PLAY")
        self.video_play_btn.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
        self.video_play_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['secondary']}, stop:1 {COLORS['accent_purple']});
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
                    stop:0 {COLORS['accent_purple']}, stop:1 {COLORS['primary']});
            }}
        """)
        self.video_play_btn.clicked.connect(self.toggle_video)
        video_layout.addWidget(self.video_play_btn, alignment=Qt.AlignCenter)

        self.video_widget.hide()
        self.content_layout.addWidget(self.video_widget)

        layout.addWidget(self.content_area)
        layout.addStretch()

    def show_image(self, base64_data):
        self.placeholder.hide()
        self.audio_widget.hide()
        self.video_widget.hide()
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
        self.video_widget.hide()
        self.audio_widget.show()
        self.current_media_type = "audio"

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
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.temp_audio_file)))

        self.is_playing = False
        self.play_pause_btn.setText("PLAY")

    def toggle_audio(self):
        if not self.media_player:
            return

        if self.is_playing:
            self.media_player.pause()
            self.play_pause_btn.setText("PLAY")
        else:
            self.media_player.play()
            self.play_pause_btn.setText("PAUSE")

        self.is_playing = not self.is_playing

    def show_video(self, base64_data):
        self.placeholder.hide()
        self.image_label.hide()
        self.audio_widget.hide()
        self.video_widget.show()
        self.current_media_type = "video"

        if base64_data.startswith("VIDEO:"):
            base64_data = base64_data[6:]

        video_bytes = base64.b64decode(base64_data)

        if self.temp_video_file:
            try:
                os.remove(self.temp_video_file)
            except:
                pass

        fd, self.temp_video_file = tempfile.mkstemp(suffix=".mp4")
        with os.fdopen(fd, 'wb') as f:
            f.write(video_bytes)

        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_display)
        self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.temp_video_file)))

        self.is_playing = False
        self.video_play_btn.setText("PLAY")

    def toggle_video(self):
        if not self.media_player:
            return

        if self.is_playing:
            self.media_player.pause()
            self.video_play_btn.setText("PLAY")
        else:
            self.media_player.play()
            self.video_play_btn.setText("PAUSE")

        self.is_playing = not self.is_playing
