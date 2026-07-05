from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QTextEdit,
    QProgressBar,
    QVBoxLayout,
    QHBoxLayout,
    QStatusBar,
    QToolBar,
)
from PySide6.QtGui import QAction


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("RadioVision V2")
        self.resize(1200, 800)

        self._create_toolbar()
        self._create_statusbar()
        self._create_ui()

    def _create_toolbar(self):

        toolbar = QToolBar("Principal")
        toolbar.setMovable(False)

        self.addToolBar(toolbar)

        self.action_start = QAction("▶ Démarrer", self)
        self.action_stop = QAction("⏹ Arrêter", self)

        toolbar.addAction(self.action_start)
        toolbar.addAction(self.action_stop)

    def _create_statusbar(self):

        self.status = QStatusBar()

        self.setStatusBar(self.status)

        self.status.showMessage("Prêt")

    def _create_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        self.state = QLabel("🟢 En attente")
        self.state.setAlignment(Qt.AlignCenter)

        self.volume = QProgressBar()
        self.volume.setRange(0, 100)

        buttons = QHBoxLayout()

        self.start_button = QPushButton("▶ Démarrer")
        self.stop_button = QPushButton("⏹ Arrêter")

        buttons.addWidget(self.start_button)
        buttons.addWidget(self.stop_button)

        self.radio_log = QTextEdit()
        self.radio_log.setReadOnly(True)

        self.code = QLabel("📟 Code : Aucun")
        self.signification = QLabel("📖 Signification : -")

        layout.addWidget(self.state)
        layout.addWidget(self.volume)
        layout.addLayout(buttons)
        layout.addWidget(self.radio_log)
        layout.addWidget(self.code)
        layout.addWidget(self.signification)

        self.action_start.triggered.connect(self.start_button.click)
        self.action_stop.triggered.connect(self.stop_button.click)