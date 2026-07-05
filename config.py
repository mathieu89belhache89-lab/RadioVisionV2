from pathlib import Path

APP_NAME = "RadioVision"
APP_VERSION = "3.0.0"

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"
ASSETS_DIR = BASE_DIR / "assets"

WINDOW_TITLE = f"{APP_NAME} {APP_VERSION}"

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800

SAMPLE_RATE = 48000
CHANNELS = 2

WHISPER_MODEL = "base"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

TEMP_AUDIO_FILE = TEMP_DIR / "capture.wav"

for folder in (
    DATA_DIR,
    LOG_DIR,
    TEMP_DIR,
    ASSETS_DIR,
):
    folder.mkdir(parents=True, exist_ok=True)