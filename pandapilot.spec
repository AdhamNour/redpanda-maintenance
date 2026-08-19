# -*- mode: python ; coding: utf-8 -*-
# PandaPilot - PyInstaller Build Specification
# Run: pyinstaller pandapilot.spec

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# ─────────────────────────────────────────────
# Resolve project root
# ─────────────────────────────────────────────
ROOT = Path(SPECPATH)

# ─────────────────────────────────────────────
# Collect PySide6 components needed for QML
# ─────────────────────────────────────────────
pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all('PySide6')

# Additional hidden imports for SSH and crypto dependencies
hidden_imports = [
    # PySide6 QML modules
    'PySide6.QtQuick',
    'PySide6.QtQml',
    'PySide6.QtQuickControls2',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
    'PySide6.QtCore',
    'PySide6.QtNetwork',
    'PySide6.QtSvg',
    # SSH & Crypto
    'paramiko',
    'paramiko.transport',
    'paramiko.sftp_client',
    'cryptography',
    'cryptography.hazmat.primitives.asymmetric',
    'cryptography.hazmat.primitives.asymmetric.rsa',
    'cryptography.hazmat.primitives.asymmetric.ed25519',
    'cryptography.hazmat.primitives.asymmetric.ecdsa',
    'cryptography.hazmat.backends.openssl',
    'bcrypt',
    # Standard library - sometimes missed
    'sqlite3',
    'threading',
    'queue',
    'socket',
    'ssl',
]
hidden_imports += pyside6_hiddenimports

# ─────────────────────────────────────────────
# Data files to bundle
# ─────────────────────────────────────────────
app_datas = [
    # QML UI files
    (str(ROOT / 'app' / 'qml'), 'app/qml'),
    # App resources (icon, etc.)
    (str(ROOT / 'app' / 'resources'), 'app/resources'),
]
app_datas += pyside6_datas

# ─────────────────────────────────────────────
# Platform-specific icon path
# ─────────────────────────────────────────────
if sys.platform == 'win32':
    icon_path = str(ROOT / 'app' / 'resources' / 'icon.ico')
elif sys.platform == 'darwin':
    icon_path = str(ROOT / 'app' / 'resources' / 'icon.icns')
else:
    icon_path = str(ROOT / 'app' / 'resources' / 'icon.png')

# ─────────────────────────────────────────────
# Analysis
# ─────────────────────────────────────────────
a = Analysis(
    [str(ROOT / 'app' / 'main.py')],
    pathex=[str(ROOT)],
    binaries=pyside6_binaries,
    datas=app_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test and dev modules from bundle
        'unittest',
        'pytest',
        'IPython',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL._tkinter_finder',
    ],
    noarchive=False,
    optimize=1,
)

# ─────────────────────────────────────────────
# PYZ Archive
# ─────────────────────────────────────────────
pyz = PYZ(a.pure)

# ─────────────────────────────────────────────
# Executable
# ─────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PandaPilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
    version_file=None,
)

# ─────────────────────────────────────────────
# COLLECT: One-dir bundle (all deps alongside exe)
# ─────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PandaPilot',
)

# ─────────────────────────────────────────────
# macOS .app BUNDLE (only created on macOS)
# ─────────────────────────────────────────────
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='PandaPilot.app',
        icon=icon_path,
        bundle_identifier='com.pandapilot.desktop',
        info_plist={
            'CFBundleName': 'PandaPilot',
            'CFBundleDisplayName': 'PandaPilot',
            'CFBundleShortVersionString': os.environ.get('APP_VERSION', '1.0.0'),
            'CFBundleVersion': os.environ.get('APP_VERSION', '1.0.0'),
            'CFBundleIconFile': 'icon.icns',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,  # Allow dark mode
            'LSMinimumSystemVersion': '12.0',
            'NSHumanReadableCopyright': 'Copyright © 2024 PandaPilot',
            'NSAppleScriptEnabled': False,
            'NSPrincipalClass': 'NSApplication',
        },
    )
