from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("RadioVision")
        self.resize(1040, 760)

        self._build_actions()
        self._build_toolbar()
        self._build_ui()

        self.status = self.statusBar()
        self.status.showMessage("Prêt")

    def _build_actions(self):
        self.action_start = QAction("Démarrer", self)
        self.action_stop = QAction("Arrêter", self)

    def _build_toolbar(self):
        toolbar = self.addToolBar("RadioVision")
        toolbar.setMovable(False)

        toolbar.addAction(self.action_start)
        toolbar.addAction(self.action_stop)

    def _build_ui(self):
        self.tabs = QTabWidget()

        self.tabs.addTab(self._build_radio_tab(), "Radio")
        self.tabs.addTab(self._build_details_tab(), "Poursuite")
        self.tabs.addTab(self._build_history_tab(), "Historique poursuites")
        self.tabs.addTab(self._build_settings_tab(), "Paramètres")

        self.setCentralWidget(self.tabs)

    def _build_radio_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        top_bar = QHBoxLayout()

        self.state = QLabel("🔴 Arrêtée")
        self.state.setObjectName("stateLabel")
        self.state.setMinimumWidth(120)

        self.volume = QProgressBar()
        self.volume.setRange(0, 100)
        self.volume.setValue(0)
        self.volume.setTextVisible(False)
        self.volume.setFixedWidth(180)

        self.start_button = QPushButton("▶ Démarrer")
        self.stop_button = QPushButton("⏹ Arrêter")

        top_bar.addWidget(self.state)
        top_bar.addWidget(QLabel("Volume"))
        top_bar.addWidget(self.volume)
        top_bar.addStretch()
        top_bar.addWidget(self.start_button)
        top_bar.addWidget(self.stop_button)

        info_bar = QHBoxLayout()

        self.code = QLabel("📟 Code : -")
        self.signification = QLabel("📖 Signification : -")

        info_bar.addWidget(self.code)
        info_bar.addWidget(self.signification)
        info_bar.addStretch()

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)

        self.radio_log = QTextEdit()
        self.radio_log.setReadOnly(True)
        self.radio_log.setPlaceholderText("Transcriptions radio...")
        self.radio_log.setObjectName("radioLog")

        layout.addLayout(top_bar)
        layout.addLayout(info_bar)
        layout.addWidget(separator)
        layout.addWidget(self.radio_log)

        return page

    def _build_details_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setObjectName("detailsLog")
        self.details.setHtml("""
        <html>
            <body style="
                background-color:#1e1f22;
                color:#dbdee1;
                font-family:Segoe UI, Arial;
                font-size:13px;
                margin:0;
                padding:0;
            ">
            </body>
        </html>
        """)

        layout.addWidget(self.details)

        return page

    def _build_history_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 12, 12, 12)

        self.pursuit_history = QTextEdit()
        self.pursuit_history.setReadOnly(True)
        self.pursuit_history.setObjectName("pursuitHistory")
        self.pursuit_history.setHtml("""
        <html>
            <body style="
                background-color:#1e1f22;
                color:#dbdee1;
                font-family:Segoe UI, Arial;
                font-size:13px;
                margin:0;
                padding:0;
            ">
                <div style="color:#949ba4; padding:8px;">
                    Aucune poursuite pour le moment.
                </div>
            </body>
        </html>
        """)

        layout.addWidget(self.pursuit_history)

        return page

    def _build_settings_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        overlay_group = QGroupBox("Overlay")
        overlay_form = QFormLayout(overlay_group)

        self.setting_overlay_enabled = QCheckBox("Activer l’overlay")
        self.setting_overlay_enabled.setChecked(True)

        self.setting_overlay_duration = QSpinBox()
        self.setting_overlay_duration.setRange(3, 60)
        self.setting_overlay_duration.setSuffix(" sec")
        self.setting_overlay_duration.setValue(15)

        self.setting_overlay_position = QComboBox()
        self.setting_overlay_position.addItem("Haut droite", "top_right")
        self.setting_overlay_position.addItem("Haut gauche", "top_left")
        self.setting_overlay_position.addItem("Bas droite", "bottom_right")
        self.setting_overlay_position.addItem("Bas gauche", "bottom_left")

        overlay_form.addRow("", self.setting_overlay_enabled)
        overlay_form.addRow("Durée affichage", self.setting_overlay_duration)
        overlay_form.addRow("Position", self.setting_overlay_position)

        analyse_group = QGroupBox("Analyse radio")
        analyse_form = QFormLayout(analyse_group)

        self.setting_pending_delay = QSpinBox()
        self.setting_pending_delay.setRange(1, 15)
        self.setting_pending_delay.setSuffix(" sec")
        self.setting_pending_delay.setValue(6)

        self.setting_merge_window = QSpinBox()
        self.setting_merge_window.setRange(2, 20)
        self.setting_merge_window.setSuffix(" sec")
        self.setting_merge_window.setValue(8)

        self.setting_pursuit_window = QSpinBox()
        self.setting_pursuit_window.setRange(1, 10)
        self.setting_pursuit_window.setSuffix(" min")
        self.setting_pursuit_window.setValue(3)

        self.setting_whisper_model = QComboBox()
        self.setting_whisper_model.addItem("Tiny — rapide mais moins précis", "tiny")
        self.setting_whisper_model.addItem("Base — équilibré", "base")
        self.setting_whisper_model.addItem("Small — plus précis mais plus lent", "small")

        analyse_form.addRow("Attente avant bulle incomplète", self.setting_pending_delay)
        analyse_form.addRow("Fenêtre fusion", self.setting_merge_window)
        analyse_form.addRow("Durée poursuite active", self.setting_pursuit_window)
        analyse_form.addRow("Modèle Whisper", self.setting_whisper_model)

        note = QLabel(
            "Note : le modèle Whisper change au prochain redémarrage de l’écoute."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color:#949ba4;")

        buttons = QHBoxLayout()

        self.setting_apply_button = QPushButton("💾 Appliquer")
        self.setting_reset_button = QPushButton("↩ Réinitialiser")
        self.setting_status = QLabel("")

        buttons.addWidget(self.setting_apply_button)
        buttons.addWidget(self.setting_reset_button)
        buttons.addStretch()

        layout.addWidget(overlay_group)
        layout.addWidget(analyse_group)
        layout.addWidget(note)
        layout.addLayout(buttons)
        layout.addWidget(self.setting_status)
        layout.addStretch()

        return page

    def _set_combo_value(self, combo, value):
        index = combo.findData(value)

        if index >= 0:
            combo.setCurrentIndex(index)

    def get_settings_values(self):
        return {
            "overlay_enabled": self.setting_overlay_enabled.isChecked(),
            "overlay_duration": self.setting_overlay_duration.value(),
            "overlay_position": self.setting_overlay_position.currentData(),
            "pending_delay": self.setting_pending_delay.value(),
            "merge_window": self.setting_merge_window.value(),
            "pursuit_window": self.setting_pursuit_window.value(),
            "whisper_model": self.setting_whisper_model.currentData(),
        }

    def set_settings_values(self, settings):
        self.setting_overlay_enabled.setChecked(
            bool(settings.get("overlay_enabled", True))
        )

        self.setting_overlay_duration.setValue(
            int(settings.get("overlay_duration", 15))
        )

        self._set_combo_value(
            self.setting_overlay_position,
            settings.get("overlay_position", "top_right"),
        )

        self.setting_pending_delay.setValue(
            int(settings.get("pending_delay", 6))
        )

        self.setting_merge_window.setValue(
            int(settings.get("merge_window", 8))
        )

        self.setting_pursuit_window.setValue(
            int(settings.get("pursuit_window", 3))
        )

        self._set_combo_value(
            self.setting_whisper_model,
            settings.get("whisper_model", "base"),
        )