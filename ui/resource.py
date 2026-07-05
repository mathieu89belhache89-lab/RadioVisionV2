from pathlib import Path

from config import ASSETS_DIR


class Resources:

    ICONS = ASSETS_DIR / "icons"
    IMAGES = ASSETS_DIR / "images"

    @staticmethod
    def icon(name: str) -> Path:
        return Resources.ICONS / name

    @staticmethod
    def image(name: str) -> Path:
        return Resources.IMAGES / name