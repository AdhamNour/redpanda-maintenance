import sys
from pathlib import Path
from typing import Optional, Tuple
from PySide6.QtCore import QObject, QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QSystemTrayIcon


def get_or_generate_app_icon(size: int = 256) -> QIcon:
    """
    Returns the official PandaPilot app icon. If the file doesn't exist on disk,
    it dynamically generates the high-res icon matching the program's branding
    and saves it to `app/resources/icon.png`.
    """
    resources_dir = Path(__file__).parent.parent / "resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    icon_file = resources_dir / "icon.png"

    if icon_file.exists():
        return QIcon(str(icon_file))

    # Generate the PandaPilot icon matching the UI logo
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    scale = size / 256.0

    # 1. Vibrant Redpanda Coral Rounded Background Squircle
    painter.setBrush(QBrush(QColor("#F04D23")))
    painter.setPen(Qt.NoPen)
    radius = 58 * scale
    painter.drawRoundedRect(QRectF(8 * scale, 8 * scale, 240 * scale, 240 * scale), radius, radius)

    # 2. Panda Ears (Dark Purple/Slate)
    ear_color = QColor("#40365F")
    painter.setBrush(QBrush(ear_color))
    # Left Ear
    painter.drawEllipse(QPointF(80 * scale, 90 * scale), 28 * scale, 28 * scale)
    # Right Ear
    painter.drawEllipse(QPointF(176 * scale, 90 * scale), 28 * scale, 28 * scale)

    # Inner Ears (Lavender accent)
    inner_ear_color = QColor("#8D7EAA")
    painter.setBrush(QBrush(inner_ear_color))
    painter.drawEllipse(QPointF(80 * scale, 90 * scale), 14 * scale, 14 * scale)
    painter.drawEllipse(QPointF(176 * scale, 90 * scale), 14 * scale, 14 * scale)

    # 3. Panda Head (Soft Lavender-White)
    head_color = QColor("#EFEBF9")
    painter.setBrush(QBrush(head_color))
    painter.drawEllipse(QPointF(128 * scale, 145 * scale), 70 * scale, 60 * scale)

    # 4. Eye Patches (Dark Slate/Purple tilted ovals)
    painter.setBrush(QBrush(ear_color))
    # Left eye patch
    painter.save()
    painter.translate(98 * scale, 138 * scale)
    painter.rotate(-15)
    painter.drawEllipse(QRectF(-18 * scale, -22 * scale, 36 * scale, 44 * scale))
    painter.restore()

    # Right eye patch
    painter.save()
    painter.translate(158 * scale, 138 * scale)
    painter.rotate(15)
    painter.drawEllipse(QRectF(-18 * scale, -22 * scale, 36 * scale, 44 * scale))
    painter.restore()

    # 5. Eye pupils & sparkles
    pupil_color = QColor("#1D1830")
    highlight_color = QColor("#FFFFFF")
    painter.setBrush(QBrush(pupil_color))
    painter.drawEllipse(QPointF(98 * scale, 138 * scale), 9 * scale, 9 * scale)
    painter.drawEllipse(QPointF(158 * scale, 138 * scale), 9 * scale, 9 * scale)

    painter.setBrush(QBrush(highlight_color))
    painter.drawEllipse(QPointF(101 * scale, 135 * scale), 3.5 * scale, 3.5 * scale)
    painter.drawEllipse(QPointF(161 * scale, 135 * scale), 3.5 * scale, 3.5 * scale)

    # 6. Blush Cheeks (Cute soft pink)
    blush_color = QColor(255, 160, 175, 170)
    painter.setBrush(QBrush(blush_color))
    painter.drawEllipse(QPointF(78 * scale, 156 * scale), 12 * scale, 8 * scale)
    painter.drawEllipse(QPointF(178 * scale, 156 * scale), 12 * scale, 8 * scale)

    # 7. Muzzle & Cute Nose
    nose_color = QColor("#2A2244")
    painter.setBrush(QBrush(nose_color))
    painter.drawEllipse(QPointF(128 * scale, 150 * scale), 9 * scale, 6.5 * scale)

    # Mouth line
    painter.setPen(QPen(nose_color, 2.5 * scale, Qt.SolidLine, Qt.RoundCap))
    painter.drawLine(QPointF(128 * scale, 156.5 * scale), QPointF(128 * scale, 162 * scale))
    painter.drawArc(QRectF(117 * scale, 157 * scale, 11 * scale, 8 * scale), 0 * 16, -180 * 16)
    painter.drawArc(QRectF(128 * scale, 157 * scale, 11 * scale, 8 * scale), 0 * 16, -180 * 16)

    painter.end()

    # Save to disk
    try:
        pixmap.save(str(icon_file), "PNG")
    except Exception as e:
        print(f"[get_or_generate_app_icon] Could not save icon.png: {e}", file=sys.stderr)

    return QIcon(pixmap)


class NotificationManager(QObject):
    """Manages cross-platform native Windows and macOS desktop notifications via QSystemTrayIcon."""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._tray_icon: Optional[QSystemTrayIcon] = None
        self._setup_tray_icon()

    def _setup_tray_icon(self) -> None:
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self._tray_icon = QSystemTrayIcon(self)
                icon = get_or_generate_app_icon()
                self._tray_icon.setIcon(icon)
                self._tray_icon.setToolTip("PandaPilot - Redpanda Maintenance Cockpit")
                self._tray_icon.show()
        except Exception as e:
            print(f"[NotificationManager] Could not initialize system tray: {e}", file=sys.stderr)

    def notify(
        self,
        title: str,
        message: str,
        level: str = "warning",
        timeout_ms: int = 6000
    ) -> None:
        """
        Displays a native desktop notification (Windows Toast / macOS Notification Center).
        """
        icon_type = QSystemTrayIcon.MessageIcon.Warning
        lvl = level.lower()
        if lvl in ("critical", "error"):
            icon_type = QSystemTrayIcon.MessageIcon.Critical
        elif lvl in ("info", "success"):
            icon_type = QSystemTrayIcon.MessageIcon.Information

        if self._tray_icon and self._tray_icon.isVisible():
            self._tray_icon.showMessage(title, message, icon_type, timeout_ms)
        else:
            print(f"[Desktop Notification] [{level.upper()}] {title} - {message}", file=sys.stderr)
