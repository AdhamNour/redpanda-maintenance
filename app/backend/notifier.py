import sys
from pathlib import Path
from typing import Any, Optional, Tuple
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

    # Ensure a QGuiApplication exists before creating QPixmap / QPainter
    from PySide6.QtGui import QGuiApplication
    _app = QGuiApplication.instance()
    if _app is None:
        _app = QGuiApplication(sys.argv if hasattr(sys, "argv") else [])

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


from PySide6.QtGui import QAction, QBrush, QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class NotificationManager(QObject):
    """Manages cross-platform native Windows and macOS desktop notifications and interactive system tray menu."""

    def __init__(self, parent: Optional[QObject] = None, controller: Optional[Any] = None):
        super().__init__(parent)
        self._controller: Optional[Any] = controller
        self._window: Optional[Any] = None
        self._tray_icon: Optional[QSystemTrayIcon] = None
        self._menu: Optional[QMenu] = None
        self._setup_tray_icon()

    def set_controller(self, controller: Any) -> None:
        self._controller = controller
        self.update_menu()

    def set_window(self, window: Any) -> None:
        self._window = window

    def show_window(self) -> None:
        """Restores and brings the main application window to the foreground."""
        if self._window:
            try:
                self._window.show()
                self._window.raise_()
                self._window.requestActivate()
            except Exception as e:
                print(f"[NotificationManager] Error activating window: {e}", file=sys.stderr)

    def _setup_tray_icon(self) -> None:
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self._tray_icon = QSystemTrayIcon(self)
                icon = get_or_generate_app_icon()
                self._tray_icon.setIcon(icon)
                self._tray_icon.setToolTip("PandaPilot - Redpanda Maintenance Cockpit")
                self._tray_icon.activated.connect(self._on_tray_activated)
                self.update_menu()
                self._tray_icon.show()
        except Exception as e:
            print(f"[NotificationManager] Could not initialize system tray: {e}", file=sys.stderr)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_window()

    def update_menu(self) -> None:
        """Rebuilds the interactive tray context menu with live cluster state."""
        if not self._tray_icon:
            return

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #161622;
                color: #FFFFFF;
                border: 1px solid #343448;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #26263A;
                color: #F04D23;
            }
            QMenu::separator {
                height: 1px;
                background: #28283A;
                margin: 4px 6px;
            }
            QMenu::item:disabled {
                color: #71717A;
            }
        """)

        # 1. Live Status Header
        status_text = "⚪ PandaPilot (Disconnected)"
        if self._controller:
            prof = getattr(self._controller, "currentProfile", None)
            prof_name = prof.get("name", "Cluster") if prof else "Cluster"
            if getattr(self._controller, "isBusy", False):
                status_text = f"⏳ {prof_name}: Processing..."
            elif getattr(self._controller, "isConnected", False):
                brokers = getattr(self._controller, "brokers", [])
                health = getattr(self._controller, "healthInfo", {})
                is_healthy = health.get("is_healthy", True) if isinstance(health, dict) else True
                health_txt = "Healthy" if is_healthy else "Degraded"
                status_text = f"🟢 {prof_name} ({len(brokers)} Nodes, {health_txt})"

        header_action = QAction(status_text, menu)
        header_font = QFont()
        header_font.setBold(True)
        header_action.setFont(header_font)
        header_action.setEnabled(False)
        menu.addAction(header_action)
        menu.addSeparator()

        # 2. Window Cockpit Action
        open_action = QAction("🪟 Open Cockpit", menu)
        open_action.triggered.connect(self.show_window)
        menu.addAction(open_action)

        if self._controller:
            # 3. Refresh Health Action
            is_conn = getattr(self._controller, "isConnected", False)
            is_busy = getattr(self._controller, "isBusy", False)

            refresh_action = QAction("🔄 Refresh Health", menu)
            refresh_action.setEnabled(is_conn and not is_busy)
            refresh_action.triggered.connect(self._controller.refreshAllClusterData)
            menu.addAction(refresh_action)

            menu.addSeparator()

            # 4. Quick Node Maintenance Submenu
            brokers = getattr(self._controller, "brokers", [])
            maint_menu = menu.addMenu("🛠️ Node Maintenance")
            maint_menu.setEnabled(is_conn and len(brokers) > 0 and not is_busy)

            if is_conn and brokers:
                for b in brokers:
                    node_id = b.get("id", 0)
                    host = b.get("host", "0.0.0.0")
                    maint_state = (b.get("maintenance_state") or "DISABLED").upper()
                    in_maint = maint_state in ("IN MAINTENANCE", "DRAINING")

                    icon_prefix = "🛠️" if in_maint else "🟢"
                    action_label = "Exit Maintenance" if in_maint else "Enter Maintenance"
                    node_action = QAction(f"{icon_prefix} Node {node_id} ({host}) - {action_label}", maint_menu)

                    def make_maint_handler(nid=node_id, draining=in_maint):
                        return lambda: (
                            self._controller.disableMaintenance(nid)
                            if draining
                            else self._controller.enableMaintenance(nid)
                        )

                    node_action.triggered.connect(make_maint_handler(node_id, in_maint))
                    maint_menu.addAction(node_action)
            else:
                empty_maint = QAction("Connect to view nodes", maint_menu)
                empty_maint.setEnabled(False)
                maint_menu.addAction(empty_maint)

            # 5. Switch Cluster Submenu
            profiles = getattr(self._controller, "profiles", [])
            current_prof = getattr(self._controller, "currentProfile", {})
            curr_id = current_prof.get("id", -1) if current_prof else -1

            cluster_menu = menu.addMenu("🌐 Switch Cluster")
            if profiles:
                for p in profiles:
                    pid = p.get("id")
                    pname = p.get("name", "Untitled")
                    is_active = (pid == curr_id)
                    prefix = "✓ " if is_active else "   "
                    prof_action = QAction(f"{prefix}{pname}", cluster_menu)

                    def make_profile_handler(profile_id=pid):
                        return lambda: self._controller.selectProfile(profile_id)

                    prof_action.triggered.connect(make_profile_handler(pid))
                    cluster_menu.addAction(prof_action)

            menu.addSeparator()

            # 6. Quick Connect / Disconnect Toggle
            if is_conn:
                conn_action = QAction("🔌 Disconnect", menu)
                conn_action.triggered.connect(self._controller.disconnectSSH)
            else:
                conn_action = QAction("⚡ Connect Cluster", menu)
                conn_action.setEnabled(not is_busy)
                conn_action.triggered.connect(self._controller.connectCurrentProfile)
            menu.addAction(conn_action)

        menu.addSeparator()

        # 7. Quit Application
        quit_action = QAction("❌ Quit PandaPilot", menu)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        self._menu = menu
        self._tray_icon.setContextMenu(self._menu)

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
