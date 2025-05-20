import os

# --- Asset Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")

# --- Colors ---
WINDOW_BG_COLOR = "#01161e"
WINDOW_SEC_BG_COLOR = "#202c39"
BOX_BG_COLOR = "#202c39"
BUTTON_PRIMARY_COLOR = "#598392"
BUTTON_HOVER_COLOR = "#124559"
ACCENT_COLOR = "#124559"
HEADING_TEXT_COLOR = "#aec3b0"
CHILD_TEXT_COLOR = "#eff6e0"
SUB_CHILD_TEXT_COLOR = "#f7ffe0"
PLACEHOLDER_TEXT_COLOR = "#708090"

# --- Window Sizes ---
MAIN_WINDOW_WIDTH = 960
MAIN_WINDOW_HEIGHT = 540
POPUP_WINDOW_WIDTH = 450
POPUP_WINDOW_HEIGHT = 250

# --- Fonts ---
POPPINS_BOLD_PATH = os.path.join(FONTS_DIR, "Poppins-Bold.ttf")
POPPINS_REGULAR_PATH = os.path.join(FONTS_DIR, "Poppins-Regular.ttf")
POPPINS_LIGHT_PATH = os.path.join(FONTS_DIR, "Poppins-Light.ttf")
POPPINS_SEMIBOLD_PATH = os.path.join(FONTS_DIR, "Poppins-SemiBold.ttf")
FONT_FAMILY_POPPINS = "Poppins"

HEADING_FONT_TUPLE = (FONT_FAMILY_POPPINS, 24, "bold")
SUB_HEADING_FONT_TUPLE = (FONT_FAMILY_POPPINS, 20, "bold")
LIBRARY_NAME_FONT_TUPLE = (FONT_FAMILY_POPPINS, 16, "bold")
LIBRARY_LINK_FONT_TUPLE = (FONT_FAMILY_POPPINS, 12)
BODY_FONT_TUPLE = (FONT_FAMILY_POPPINS, 14)
BUTTON_FONT_TUPLE = (FONT_FAMILY_POPPINS, 14, "bold")

# --- Icons ---
APP_ICON_PATH = os.path.join(ICONS_DIR, "app_icon.ico")
AUDIO_ICON_PATH = os.path.join(ICONS_DIR, "audio_icon.png")
VIDEO_ICON_PATH = os.path.join(ICONS_DIR, "video_icon.png")
CLOSE_ICON_PATH = os.path.join(ICONS_DIR, "close.png")
MINIMIZE_ICON_PATH = os.path.join(ICONS_DIR, "minus.png")

# --- UI Styles ---
DEFAULT_BUTTON_STYLE = {
    "fg_color": BUTTON_PRIMARY_COLOR,
    "hover_color": BUTTON_HOVER_COLOR,
    "text_color": CHILD_TEXT_COLOR,
    "corner_radius": 8,
}

SCROLLABLE_FRAME_STYLE = {
    "fg_color": BOX_BG_COLOR,
    "corner_radius": 10,
}

# --- App Info ---
APP_NAME = "Speech to Text Transcription Simple Tool"

LIBRARIES_USED = [
    ("OpenAI Whisper", "https://github.com/openai/whisper", LIBRARY_NAME_FONT_TUPLE, LIBRARY_LINK_FONT_TUPLE),
    ("CustomTkinter", "https://github.com/TomSchimansky/CustomTkinter", LIBRARY_NAME_FONT_TUPLE, LIBRARY_LINK_FONT_TUPLE),
    ("python-docx", "https://python-docx.readthedocs.io/", LIBRARY_NAME_FONT_TUPLE, LIBRARY_LINK_FONT_TUPLE),
    ("FPDF2", "https://github.com/py-pdf/fpdf2", LIBRARY_NAME_FONT_TUPLE, LIBRARY_LINK_FONT_TUPLE),
    ("FFmpeg", "https://ffmpeg.org/", LIBRARY_NAME_FONT_TUPLE, LIBRARY_LINK_FONT_TUPLE),
    ("Pillow (PIL)", "https://python-pillow.org/", LIBRARY_NAME_FONT_TUPLE, LIBRARY_LINK_FONT_TUPLE),
]

DEFAULT_WHISPER_MODEL = "base"
