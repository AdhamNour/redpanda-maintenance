# 🐼 PandaPilot

**PandaPilot** is a native desktop application for Redpanda cluster operations, health diagnostics, and safe rolling maintenance built with **Python (PySide6 / Qt Quick QML)**, **Paramiko** (SSH), and **SQLite**.

---

## ✨ Features

* **🖥️ Interactive Cluster Dashboard**: Visual broker cards displaying Controller status (`★ Controller`), IP/port, Rack ID, and live maintenance states.
* **🛡️ Safe Maintenance Mode Operations**: One-click node draining and maintenance management with asynchronous non-blocking `--wait` execution.
* **🩺 Health & Diagnostic Matrix**: Real-time partition health tracking (Under-replicated, Leaderless, Offline partitions) and `rpk cluster health` output inspector.
* **🛠️ Guided Rolling Upgrade Assistant**: Step-by-step wizard for performing zero-downtime rolling node upgrades.
* **💾 Multi-Profile SQLite Storage**: Cluster credentials (SSH password or private keys, Redpanda SASL) persisted in SQLite under the user's Documents folder (`~/Documents/PandaPilot/pandapilot.db`).
* **📜 Live Console & Output Stream**: Collapsible drawer streaming SSH stdout and stderr with timestamps and status badges in real time.

---

## 🚀 Installation & Running

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
python -m app.main
```
Or directly:
```bash
python app/main.py
```

---

## 🗂️ Project Structure

```
redpanda-maintenance/
├── app/
│   ├── main.py                     # Desktop application entrypoint & QML engine setup
│   ├── backend/
│   │   ├── controller.py           # PySide6 QObject bridge between Python backend and QML UI
│   │   ├── database.py             # SQLite manager (~/Documents/PandaPilot/pandapilot.db)
│   │   ├── parser.py               # Robust parser for rpk info, health, and maintenance output
│   │   └── ssh_client.py           # Async Paramiko SSH connection & rpk execution manager
│   └── qml/
│       ├── Main.qml                # Root application window, navigation sidebar & top bar
│       ├── Theme.qml               # Modern Redpanda dark theme palette & typography
│       ├── views/
│       │   ├── DashboardView.qml   # Cluster summary cards & interactive broker grid
│       │   ├── HealthView.qml      # Health metrics & under-replicated partitions inspector
│       │   ├── MaintenanceView.qml # Maintenance matrix table & rolling maintenance wizard
│       │   └── ProfilesView.qml    # Saved connection profiles manager (Add/Edit/Delete)
│       └── components/
│           ├── BrokerCard.qml      # Interactive card representing each node
│           ├── ConfirmDialog.qml   # Safety confirmation dialog for critical operations
│           ├── LogDrawer.qml       # Collapsible live output console with ANSI/syntax styling
│           └── StatusBadge.qml     # Health/Node state indicators (Healthy, Draining, Warning)
├── simple_ssh_rpk.py               # Existing CLI maintenance script
├── tests/
│   └── test_backend.py             # Unit tests for database & parsers
├── requirements.txt
└── README.md
```

---

## 🛡️ Safety & Storage

* **Database Location**:
  * Windows: `C:\Users\<username>\Documents\PandaPilot\pandapilot.db`
  * Linux / macOS: `~/Documents/PandaPilot/pandapilot.db`
* **Activity Logs**: Every maintenance operation (enable/disable) is automatically logged to the `activity_logs` table in SQLite for auditing.
