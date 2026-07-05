import html

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class OverlayWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.display_ms = 15000

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.setFixedWidth(390)

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(12, 12, 12, 12)

        self.card = QFrame()
        self.card.setObjectName("radioOverlayCard")

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(14, 12, 14, 12)
        self.card_layout.setSpacing(8)

        self.header = QLabel()
        self.header.setObjectName("radioOverlayHeader")
        self.header.setTextFormat(Qt.RichText)

        self.content = QLabel()
        self.content.setObjectName("radioOverlayContent")
        self.content.setTextFormat(Qt.RichText)
        self.content.setWordWrap(True)

        self.card_layout.addWidget(self.header)
        self.card_layout.addWidget(self.content)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.card.setGraphicsEffect(shadow)

        self.root_layout.addWidget(self.card)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)

        self.hide()

    def priority_style(self, priority_label):
        if priority_label == "URGENT":
            return {
                "color": "#ed4245",
                "emoji": "🚨",
                "title": "URGENCE RADIO",
            }

        if priority_label == "POURSUITE":
            return {
                "color": "#faa61a",
                "emoji": "🚓",
                "title": "POURSUITE EN COURS",
            }

        if priority_label == "INCOMPLET":
            return {
                "color": "#fee75c",
                "emoji": "⚠️",
                "title": "INFO INCOMPLÈTE",
            }

        return {
            "color": "#5865f2",
            "emoji": "📡",
            "title": "INFO RADIO",
        }

    def show_radio_event(self, priority_label, priority_color, rows):
        style = self.priority_style(priority_label)
        color = style["color"]

        self.card.setStyleSheet(f"""
            QFrame#radioOverlayCard {{
                background-color: rgba(30, 31, 34, 245);
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 22);
                border-left: 5px solid {color};
            }}

            QLabel#radioOverlayHeader {{
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
            }}

            QLabel#radioOverlayContent {{
                color: #dbdee1;
                font-size: 13px;
            }}
        """)

        self.header.setText(f"""
            <div style="line-height:1.2;">
                <span style="font-size:15px;">{style["emoji"]}</span>
                <span style="color:#ffffff; font-weight:800; margin-left:4px;">
                    {style["title"]}
                </span>
                <span style="
                    color:{color};
                    font-size:11px;
                    font-weight:800;
                    margin-left:8px;
                ">
                    {priority_label}
                </span>
            </div>
        """)

        html_rows = ""

        for emoji, label, value in rows:
            label = html.escape(str(label))
            value = html.escape(html.unescape(str(value)))

            if label == "Motif":
                html_rows += f"""
                <div style="
                    background-color:rgba(255,255,255,0.045);
                    border-radius:8px;
                    padding:7px 9px;
                    margin:6px 0 8px 0;
                    color:#ffffff;
                    font-weight:600;
                ">
                    {value}
                </div>
                """
                continue

            if label == "Manquant":
                html_rows += f"""
                <div style="
                    color:#fee75c;
                    font-size:12px;
                    margin-top:6px;
                    font-weight:700;
                ">
                    ⚠️ Manquant : {value}
                </div>
                """
                continue

            html_rows += f"""
            <div style="margin:3px 0;">
                <span style="display:inline-block; width:24px;">{emoji}</span>
                <span style="color:#949ba4; font-weight:700;">
                    {label}
                </span>
                <span style="color:#dbdee1;">
                    &nbsp;{value}
                </span>
            </div>
            """

        self.content.setText(html_rows)

        self.adjustSize()
        self.move_to_top_right()

        self.show()
        self.raise_()
        self.timer.start(self.display_ms)

    def move_to_top_right(self):
        screen = QApplication.primaryScreen()

        if not screen:
            return

        geo = screen.availableGeometry()

        x = geo.right() - self.width() - 25
        y = geo.top() + 25

        self.move(x, y)