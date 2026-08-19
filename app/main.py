import os
import sys
from pathlib import Path
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import Qt

from app.backend.controller import AppController
from app.backend.database import DatabaseManager


def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("PandaPilot")
    app.setOrganizationName("PandaPilot")
    app.setApplicationDisplayName("PandaPilot - Redpanda Maintenance Cockpit")

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

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
