"""
Styles et constantes visuelles pour l'application de chat.
"""
import platform

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
