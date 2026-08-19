import sys
from typing import Optional
from PySide6.QtCore import QObject
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QSystemTrayIcon


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
                self._tray_icon.setIcon(self._create_app_icon())
                self._tray_icon.setToolTip("PandaPilot - Redpanda Maintenance Cockpit")
                self._tray_icon.show()
        except Exception as e:
            print(f"[NotificationManager] Could not initialize system tray: {e}", file=sys.stderr)

    def _create_app_icon(self) -> QIcon:
        """Generates a high-contrast Redpanda app icon for the system tray."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background rounded rect
        painter.setBrush(QColor("#F04D23"))
        painter.setPen(QColor("#D83F17"))
        painter.drawRoundedRect(4, 4, 56, 56, 14, 14)

        # Draw "P" symbol
        painter.setPen(QColor("#FFFFFF"))
        font = QFont("Segoe UI", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x0084, "P") # AlignCenter = 0x0084
        painter.end()

        return QIcon(pixmap)

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
