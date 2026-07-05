from pathlib import Path

APP_NAME = "RadioVision"
APP_VERSION = "2.0.0 Foundation"

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"
ASSETS_DIR = BASE_DIR / "assets"

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

WHISPER_MODEL = "base"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE = "int8"

SAMPLE_RATE = 48000

for folder in (
    DATA_DIR,
    LOG_DIR,
    TEMP_DIR,
):
    folder.mkdir(exist_ok=True)