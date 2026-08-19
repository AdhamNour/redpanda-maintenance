import os
import sys
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from app.backend.controller import AppController
from app.backend.database import DatabaseManager
from app.backend.notifier import get_or_generate_app_icon


def main():
    # Set Windows AppUserModelID so custom taskbar icon displays properly on Windows
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("redpanda.pandapilot.desktop.1.0")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("PandaPilot")
    app.setOrganizationName("PandaPilot")
    app.setApplicationDisplayName("PandaPilot - Redpanda Maintenance Cockpit")

    # Set Application & Window Icon
    app_icon = get_or_generate_app_icon()
    app.setWindowIcon(app_icon)

    # Initialize SQLite Database & Backend Controller
    db_manager = DatabaseManager()
    controller = AppController(db_manager)

    # Initialize QML Engine
    engine = QQmlApplicationEngine()

    # Expose AppController to QML
    engine.rootContext().setContextProperty("appController", controller)

    # Load Main.qml
    qml_path = Path(__file__).parent / "qml" / "Main.qml"
    engine.load(str(qml_path))

    if not engine.rootObjects():
        print(f"Error: Failed to load QML interface from {qml_path}", file=sys.stderr)
        sys.exit(-1)

    # Set icon and register window with controller for tray actions
    root_objects = engine.rootObjects()
    if root_objects:
        controller.set_root_window(root_objects[0])
        for root_obj in root_objects:
            if hasattr(root_obj, "setIcon"):
                root_obj.setIcon(app_icon)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
