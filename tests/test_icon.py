import unittest
from pathlib import Path
from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QIcon

from app.backend.notifier import get_or_generate_app_icon


class TestAppIcon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QCoreApplication.instance() is None:
            cls.app = QCoreApplication([])
        else:
            cls.app = QCoreApplication.instance()

    def test_icon_generation(self):
        icon = get_or_generate_app_icon(size=256)
        self.assertIsInstance(icon, QIcon)
        self.assertFalse(icon.isNull())

        icon_path = Path(__file__).parent.parent / "app" / "resources" / "icon.png"
        self.assertTrue(icon_path.exists())
        self.assertGreater(icon_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
