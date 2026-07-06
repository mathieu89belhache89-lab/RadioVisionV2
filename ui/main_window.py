from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
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
        self.tabs.addTab(self._build_learning_tab(), "Apprentissage")
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


    def _build_learning_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        self.learning_options = {}

        help_text = QLabel(
            "Ajoute ici les erreurs que Whisper entend mal. "
            "Exemple : entendu = sambi chap, type = Lieu, correction officielle = Sandy Shores."
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color:#949ba4;")

        recent_group = QGroupBox("Derniers calls entendus")
        recent_layout = QVBoxLayout(recent_group)

        self.learning_recent_list = QListWidget()
        self.learning_recent_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.learning_recent_list.setMinimumHeight(95)

        recent_buttons = QHBoxLayout()

        self.learning_use_selected_recent_button = QPushButton("↙ Utiliser la ligne sélectionnée")
        self.learning_use_last_button = QPushButton("🎙️ Utiliser le dernier call")

        recent_buttons.addWidget(self.learning_use_selected_recent_button)
        recent_buttons.addWidget(self.learning_use_last_button)
        recent_buttons.addStretch()

        recent_layout.addWidget(self.learning_recent_list)
        recent_layout.addLayout(recent_buttons)

        add_group = QGroupBox("Ajouter / modifier une correction")
        add_form = QFormLayout(add_group)

        self.learning_heard_input = QLineEdit()
        self.learning_heard_input.setPlaceholderText("Exemple : sambi chap")

        self.learning_type_combo = QComboBox()
        self.learning_type_combo.addItem("Lieu", "locations")
        self.learning_type_combo.addItem("Véhicule", "vehicles")
        self.learning_type_combo.addItem("Code radio", "codes")
        self.learning_type_combo.addItem("Incident / info", "incidents")

        self.learning_value_combo = QComboBox()
        self.learning_value_combo.setEditable(True)
        self.learning_value_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.learning_type_combo.currentIndexChanged.connect(
            self.refresh_learning_value_combo
        )

        add_form.addRow("Entendu par Whisper", self.learning_heard_input)
        add_form.addRow("Type", self.learning_type_combo)
        add_form.addRow("Correction officielle", self.learning_value_combo)

        button_row = QHBoxLayout()

        self.learning_add_button = QPushButton("➕ Ajouter")
        self.learning_update_button = QPushButton("💾 Modifier sélection")
        self.learning_delete_button = QPushButton("🗑 Supprimer sélection")
        self.learning_test_button = QPushButton("🧪 Tester")
        self.learning_reload_button = QPushButton("↻ Recharger")

        button_row.addWidget(self.learning_add_button)
        button_row.addWidget(self.learning_update_button)
        button_row.addWidget(self.learning_delete_button)
        button_row.addWidget(self.learning_test_button)
        button_row.addWidget(self.learning_reload_button)
        button_row.addStretch()

        self.learning_status = QLabel("")
        self.learning_status.setWordWrap(True)
        self.learning_status.setStyleSheet("color:#57f287;")

        list_group = QGroupBox("Corrections enregistrées")
        list_layout = QVBoxLayout(list_group)

        self.learning_corrections_table = QTableWidget(0, 3)
        self.learning_corrections_table.setHorizontalHeaderLabels([
            "Type",
            "Entendu",
            "Correction officielle",
        ])
        self.learning_corrections_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.learning_corrections_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.learning_corrections_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.learning_corrections_table.verticalHeader().setVisible(False)
        self.learning_corrections_table.horizontalHeader().setStretchLastSection(True)
        self.learning_corrections_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )
        self.learning_corrections_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )
        self.learning_corrections_table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )

        self.learning_corrections_preview = QTextEdit()
        self.learning_corrections_preview.setReadOnly(True)
        self.learning_corrections_preview.hide()

        list_layout.addWidget(self.learning_corrections_table)

        layout.addWidget(help_text)
        layout.addWidget(recent_group)
        layout.addWidget(add_group)
        layout.addLayout(button_row)
        layout.addWidget(self.learning_status)
        layout.addWidget(list_group)

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

        audio_group = QGroupBox("Source audio")
        audio_form = QFormLayout(audio_group)

        self.setting_capture_microphone = QCheckBox(
            "Inclure mon micro en plus du son PC / FiveM"
        )
        self.setting_capture_microphone.setChecked(False)

        audio_note = QLabel(
            "Conseil : utilise un casque pour éviter que ton micro reprenne le son du jeu ou de Discord."
        )
        audio_note.setWordWrap(True)
        audio_note.setStyleSheet("color:#949ba4;")

        audio_form.addRow("", self.setting_capture_microphone)
        audio_form.addRow("Note", audio_note)

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

        self.setting_strict_analysis = QCheckBox("Mode analyse stricte : ne pas afficher les lieux inconnus comme sûrs")
        self.setting_strict_analysis.setChecked(True)

        self.setting_whisper_model = QComboBox()
        self.setting_whisper_model.addItem("Tiny — rapide mais moins précis", "tiny")
        self.setting_whisper_model.addItem("Base — équilibré", "base")
        self.setting_whisper_model.addItem("Small — plus précis mais plus lent", "small")

        analyse_form.addRow("Attente avant bulle incomplète", self.setting_pending_delay)
        analyse_form.addRow("Fenêtre fusion", self.setting_merge_window)
        analyse_form.addRow("Durée poursuite active", self.setting_pursuit_window)
        analyse_form.addRow("", self.setting_strict_analysis)
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
        layout.addWidget(audio_group)
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
            "capture_microphone": self.setting_capture_microphone.isChecked(),
            "strict_analysis": self.setting_strict_analysis.isChecked(),
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

        self.setting_capture_microphone.setChecked(
            bool(settings.get("capture_microphone", False))
        )

        self.setting_strict_analysis.setChecked(
            bool(settings.get("strict_analysis", True))
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

    def set_learning_options(self, options):
        self.learning_options = options or {}
        self.refresh_learning_value_combo()

    def refresh_learning_value_combo(self):
        if not hasattr(self, "learning_value_combo"):
            return

        section = self.learning_type_combo.currentData()
        values = self.learning_options.get(section, [])

        current_text = self.learning_value_combo.currentText().strip()

        self.learning_value_combo.blockSignals(True)
        self.learning_value_combo.clear()

        for value in values:
            self.learning_value_combo.addItem(str(value))

        if current_text:
            index = self.learning_value_combo.findText(current_text)
            if index >= 0:
                self.learning_value_combo.setCurrentIndex(index)
            else:
                self.learning_value_combo.setEditText(current_text)

        self.learning_value_combo.blockSignals(False)

    def get_learning_values(self):
        return {
            "heard": self.learning_heard_input.text().strip(),
            "section": self.learning_type_combo.currentData(),
            "section_label": self.learning_type_combo.currentText(),
            "correction": self.learning_value_combo.currentText().strip(),
        }

    def set_learning_heard_text(self, text):
        self.learning_heard_input.setText(str(text or "").strip())

    def set_learning_status(self, text, error=False):
        self.learning_status.setText(str(text or ""))

        if error:
            self.learning_status.setStyleSheet("color:#ed4245;")
        else:
            self.learning_status.setStyleSheet("color:#57f287;")

    def set_corrections_preview(self, html_text):
        if hasattr(self, "learning_corrections_preview"):
            self.learning_corrections_preview.setHtml(str(html_text or ""))

    def set_recent_calls(self, calls):
        recent_list = getattr(self, "learning_recent_list", None)

        if recent_list is None:
            return

        recent_list.clear()

        if not calls:
            return

        added = set()

        for call in calls:
            current = str(call).strip()

            if not current:
                continue

            if current in added:
                continue

            added.add(current)
            recent_list.addItem(current)

    def get_selected_recent_call(self):
        if not hasattr(self, "learning_recent_list"):
            return ""

        item = self.learning_recent_list.currentItem()

        if not item:
            return ""

        return item.text().strip()

    def set_corrections_table(self, rows):
        if not hasattr(self, "learning_corrections_table"):
            return

        table = self.learning_corrections_table
        table.blockSignals(True)
        table.setRowCount(0)

        for row_data in rows or []:
            row = table.rowCount()
            table.insertRow(row)

            section = str(row_data.get("section", ""))
            label = str(row_data.get("section_label", section))
            heard = str(row_data.get("heard", ""))
            correction = str(row_data.get("correction", ""))

            values = [label, heard, correction]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(256, section)
                item.setData(257, heard)
                item.setData(258, correction)
                table.setItem(row, column, item)

        table.blockSignals(False)

    def get_selected_correction(self):
        if not hasattr(self, "learning_corrections_table"):
            return None

        table = self.learning_corrections_table
        row = table.currentRow()

        if row < 0:
            return None

        item = table.item(row, 0)

        if not item:
            return None

        return {
            "section": item.data(256),
            "heard": item.data(257),
            "correction": item.data(258),
        }

    def set_learning_type_by_section(self, section):
        index = self.learning_type_combo.findData(section)

        if index >= 0:
            self.learning_type_combo.setCurrentIndex(index)

    def set_learning_values(self, section=None, heard=None, correction=None):
        if section:
            self.set_learning_type_by_section(section)

        if heard is not None:
            self.learning_heard_input.setText(str(heard or ""))

        if correction is not None:
            correction = str(correction or "")
            index = self.learning_value_combo.findText(correction)

            if index >= 0:
                self.learning_value_combo.setCurrentIndex(index)
            else:
                self.learning_value_combo.setEditText(correction)

