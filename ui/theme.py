from PySide6.QtWidgets import QApplication


def apply_theme():

    app = QApplication.instance()

    app.setStyleSheet("""
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            font-size: 11pt;
        }

        QPushButton {
            background-color: #2d2d30;
            border: 1px solid #3f3f46;
            border-radius: 6px;
            padding: 8px;
            min-height: 36px;
        }

        QPushButton:hover {
            background-color: #3c3c42;
        }

        QLabel {
            color: white;
        }

        QTextEdit {
            background-color: #252526;
            border: 1px solid #3f3f46;
            border-radius: 6px;
        }

        QProgressBar {
            border: 1px solid #3f3f46;
            border-radius: 6px;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #00c853;
        }

        QTabWidget::pane {
            border: 1px solid #3f3f46;
        }

        QTabBar::tab {
            background: #2d2d30;
            padding: 8px 16px;
        }

        QTabBar::tab:selected {
            background: #0078d4;
        }
    """)