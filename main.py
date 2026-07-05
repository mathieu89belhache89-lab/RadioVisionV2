import sys

from PySide6.QtWidgets import QApplication

from core.app import RadioVisionApp


def main():
    app = QApplication(sys.argv)

    radio_vision = RadioVisionApp()

    radio_vision.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()