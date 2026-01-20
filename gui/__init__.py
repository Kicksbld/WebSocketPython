"""
Module GUI pour l'application de chat.
"""
from .chat_app import ChatApp
from .styles import COLORS, FONT_FAMILY, GLOBAL_STYLE
from .qt_ws_client import QtWSClient

__all__ = ['ChatApp', 'COLORS', 'FONT_FAMILY', 'GLOBAL_STYLE', 'QtWSClient']
