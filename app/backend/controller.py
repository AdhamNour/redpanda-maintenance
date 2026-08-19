import datetime
import threading
from typing import Any, Dict, List, Optional
from PySide6.QtCore import QObject, Property, Signal, Slot

from app.backend.database import DatabaseManager
from app.backend.parser import parse_brokers, parse_cluster_health, parse_maintenance_status
from app.backend.ssh_client import SSHClientManager


class AppController(QObject):
    """Main QObject controller bridging the Python backend and QML frontend."""

    # Signals
    profilesChanged = Signal()
    currentProfileChanged = Signal()
    connectionStateChanged = Signal()
    clusterDataChanged = Signal()
    healthDataChanged = Signal()
    maintenanceDataChanged = Signal()
    busyStateChanged = Signal()
    logAppended = Signal(str, str, str) # timestamp, level (INFO/SUCCESS/ERROR), message
    operationFinished = Signal(str, bool, str) # operation_name, success, message

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        super().__init__()
        self.db = db_manager or DatabaseManager()
        self.ssh = SSHClientManager()

        self._profiles: List[Dict[str, Any]] = []
        self._current_profile: Dict[str, Any] = {}
        self._is_connected: bool = False
        self._connection_status: str = "Disconnected"

        self._brokers: List[Dict[str, Any]] = []
        self._controller_broker: Dict[str, Any] = {}
        self._health_info: Dict[str, Any] = {
            "is_healthy": True,
            "status_text": "UNKNOWN",
            "under_replicated_partitions": 0,
            "leaderless_partitions": 0,
            "offline_partitions": 0,
            "raw_output": ""
        }
        self._maintenance_list: List[Dict[str, Any]] = []

        self._is_busy: bool = False
        self._busy_message: str = ""

        # Load initial profiles from database
        self.refresh_profiles_internal()

    # -------------------------------------------------------------------------
    # Properties for QML
    # -------------------------------------------------------------------------

    @Property(list, notify=profilesChanged)
    def profiles(self) -> List[Dict[str, Any]]:
        return self._profiles

    @Property(dict, notify=currentProfileChanged)
    def currentProfile(self) -> Dict[str, Any]:
        return self._current_profile

    @Property(bool, notify=connectionStateChanged)
    def isConnected(self) -> bool:
        return self._is_connected

    @Property(str, notify=connectionStateChanged)
    def connectionStatus(self) -> str:
        return self._connection_status

    @Property(list, notify=clusterDataChanged)
    def brokers(self) -> List[Dict[str, Any]]:
        return self._brokers

    @Property(dict, notify=clusterDataChanged)
    def controllerBroker(self) -> Dict[str, Any]:
        return self._controller_broker

    @Property(dict, notify=healthDataChanged)
    def healthInfo(self) -> Dict[str, Any]:
        return self._health_info

    @Property(list, notify=maintenanceDataChanged)
    def maintenanceList(self) -> List[Dict[str, Any]]:
        return self._maintenance_list

    @Property(bool, notify=busyStateChanged)
    def isBusy(self) -> bool:
        return self._is_busy

    @Property(str, notify=busyStateChanged)
    def busyMessage(self) -> str:
        return self._busy_message

    @Property(str, constant=True)
    def databasePath(self) -> str:
        return str(self.db.db_path)

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _set_busy(self, busy: bool, message: str = ""):
        self._is_busy = busy
        self._busy_message = message
        self.busyStateChanged.emit()

    def _log(self, level: str, message: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.logAppended.emit(now, level, message)

    def refresh_profiles_internal(self):
        self._profiles = self.db.get_profiles()
        self.profilesChanged.emit()

        # If current profile exists, refresh its data
        if self._current_profile:
            p_id = self._current_profile.get("id")
            updated = self.db.get_profile(p_id)
            if updated:
                self._current_profile = updated
            elif self._profiles:
                self._current_profile = self._profiles[0]
            else:
                self._current_profile = {}
        elif self._profiles:
            self._current_profile = self._profiles[0]

        self.currentProfileChanged.emit()

    # -------------------------------------------------------------------------
    # Slots callable from QML
    # -------------------------------------------------------------------------

    @Slot()
    def refreshProfiles(self):
        self.refresh_profiles_internal()

    @Slot(int)
    def selectProfile(self, profile_id: int):
        profile = self.db.get_profile(profile_id)
        if profile:
            self._current_profile = profile
            self.currentProfileChanged.emit()

    @Slot(dict, result=int)
    def addProfile(self, profile_data: dict) -> int:
        new_id = self.db.add_profile(profile_data)
        self.refresh_profiles_internal()
        self.selectProfile(new_id)
        self._log("SUCCESS", f"Created profile: {profile_data.get('name')}")
        return new_id

    @Slot(int, dict, result=bool)
    def updateProfile(self, profile_id: int, profile_data: dict) -> bool:
        ok = self.db.update_profile(profile_id, profile_data)
        self.refresh_profiles_internal()
        self._log("INFO", f"Updated profile: {profile_data.get('name')}")
        return ok

    @Slot(int, result=bool)
    def deleteProfile(self, profile_id: int) -> bool:
        ok = self.db.delete_profile(profile_id)
        self.refresh_profiles_internal()
        self._log("INFO", f"Deleted profile ID: {profile_id}")
        return ok

    @Slot()
    def connectCurrentProfile(self):
        if not self._current_profile:
            self._log("ERROR", "No cluster profile selected.")
            return

        self._set_busy(True, f"Connecting to {self._current_profile.get('name')}...")
        self._log("INFO", f"Initiating SSH connection to {self._current_profile.get('host')}:{self._current_profile.get('port', 22)}...")

        def worker():
            success, msg = self.ssh.connect(self._current_profile)
            self._is_connected = success
            self._connection_status = "Connected" if success else f"Error: {msg}"
            self.connectionStateChanged.emit()
            self._set_busy(False)

            if success:
                self._log("SUCCESS", f"Connected to {self._current_profile.get('host')}")
                self.refreshAllClusterData()
            else:
                self._log("ERROR", msg)
                self.operationFinished.emit("connect", False, msg)

        threading.Thread(target=worker, daemon=True).start()

    @Slot()
    def disconnectSSH(self):
        self.ssh.disconnect()
        self._is_connected = False
        self._connection_status = "Disconnected"
        self.connectionStateChanged.emit()
        self._log("INFO", "Disconnected from SSH host.")

    @Slot()
    def refreshAllClusterData(self):
        """Fetches brokers, health, and maintenance status asynchronously."""
        if not self._is_connected:
            return

        self._set_busy(True, "Refreshing cluster data...")

        def worker():
            sasl_flags = self.ssh.get_sasl_flags(self._current_profile)

            # 1. Fetch brokers info
            info_cmd = f"rpk cluster info {sasl_flags}"
            self._log("INFO", f"Executing: {info_cmd}")
            code, out, err = self.ssh.execute_command(info_cmd)

            if out:
                new_brokers, new_main = parse_brokers(out)
                self._brokers = new_brokers
                self._controller_broker = new_main or {}
                self.clusterDataChanged.emit()
                self._log("SUCCESS", f"Fetched {len(new_brokers)} broker(s).")
            elif err:
                self._log("ERROR", f"rpk cluster info failed: {err}")

            # 2. Fetch maintenance status to enrich broker state
            maint_cmd = f"rpk cluster maintenance status {sasl_flags}"
            code, out_m, err_m = self.ssh.execute_command(maint_cmd)
            if out_m:
                self._maintenance_list = parse_maintenance_status(out_m)
                # Enrich brokers with maintenance status
                maint_map = {m["node_id"]: m for m in self._maintenance_list}
                for b in self._brokers:
                    if b["id"] in maint_map:
                        m_info = maint_map[b["id"]]
                        b["maintenance_state"] = m_info["status"]
                        b["draining"] = m_info["draining"]
                        b["finished"] = m_info["finished"]
                self.clusterDataChanged.emit()
                self.maintenanceDataChanged.emit()

            # 3. Fetch cluster health
            health_cmd = f"rpk cluster health {sasl_flags}"
            code, out_h, err_h = self.ssh.execute_command(health_cmd)
            if out_h:
                self._health_info = parse_cluster_health(out_h)
                self.healthDataChanged.emit()

            self._set_busy(False)
            self.operationFinished.emit("refresh", True, "Cluster data refreshed.")

        threading.Thread(target=worker, daemon=True).start()

    @Slot(int)
    def enableMaintenance(self, node_id: int):
        """Puts a node into maintenance mode and waits for partition draining."""
        if not self._is_connected:
            self._log("ERROR", "Cannot enable maintenance: Not connected.")
            return

        self._set_busy(True, f"Enabling maintenance mode on Node {node_id} (Draining partitions)...")
        self._log("INFO", f"Enabling maintenance on Node {node_id} with --wait...")

        def worker():
            sasl_flags = self.ssh.get_sasl_flags(self._current_profile)
            cmd = f"rpk cluster maintenance enable {node_id} --wait {sasl_flags}"

            def on_line(line: str):
                self._log("INFO", f"[Node {node_id}] {line}")

            code, out, err = self.ssh.execute_command(cmd, on_stdout_line=on_line, on_stderr_line=on_line)

            self._set_busy(False)
            if code == 0:
                self._log("SUCCESS", f"Node {node_id} is now in maintenance mode.")
                self.db.log_activity(
                    self._current_profile.get("id"),
                    cmd,
                    "ENABLE_MAINTENANCE",
                    "SUCCESS",
                    out
                )
                self.operationFinished.emit("enable_maintenance", True, f"Node {node_id} entered maintenance mode.")
            else:
                self._log("ERROR", f"Failed to enable maintenance on Node {node_id}: {err}")
                self.db.log_activity(
                    self._current_profile.get("id"),
                    cmd,
                    "ENABLE_MAINTENANCE",
                    "FAILED",
                    err or out
                )
                self.operationFinished.emit("enable_maintenance", False, err or out)

            self.refreshAllClusterData()

        threading.Thread(target=worker, daemon=True).start()

    @Slot(int)
    def disableMaintenance(self, node_id: int):
        """Takes a node out of maintenance mode."""
        if not self._is_connected:
            self._log("ERROR", "Cannot disable maintenance: Not connected.")
            return

        self._set_busy(True, f"Disabling maintenance mode on Node {node_id}...")
        self._log("INFO", f"Disabling maintenance on Node {node_id}...")

        def worker():
            sasl_flags = self.ssh.get_sasl_flags(self._current_profile)
            cmd = f"rpk cluster maintenance disable {node_id} {sasl_flags}"

            code, out, err = self.ssh.execute_command(cmd)

            self._set_busy(False)
            if code == 0:
                self._log("SUCCESS", f"Node {node_id} maintenance mode disabled.")
                self.db.log_activity(
                    self._current_profile.get("id"),
                    cmd,
                    "DISABLE_MAINTENANCE",
                    "SUCCESS",
                    out
                )
                self.operationFinished.emit("disable_maintenance", True, f"Node {node_id} exited maintenance mode.")
            else:
                self._log("ERROR", f"Failed to disable maintenance on Node {node_id}: {err}")
                self.db.log_activity(
                    self._current_profile.get("id"),
                    cmd,
                    "DISABLE_MAINTENANCE",
                    "FAILED",
                    err or out
                )
                self.operationFinished.emit("disable_maintenance", False, err or out)

            self.refreshAllClusterData()

        threading.Thread(target=worker, daemon=True).start()

    @Slot(str)
    def executeCustomCommand(self, cmd: str):
        """Executes a custom shell command over SSH."""
        if not self._is_connected:
            self._log("ERROR", "Cannot execute command: Not connected.")
            return

        self._log("INFO", f"Executing custom command: {cmd}")

        def worker():
            def on_out(line: str):
                self._log("INFO", line)

            def on_err(line: str):
                self._log("ERROR", line)

            code, out, err = self.ssh.execute_command(cmd, on_stdout_line=on_out, on_stderr_line=on_err)
            if code == 0:
                self._log("SUCCESS", f"Command completed (Exit Code: {code})")
            else:
                self._log("ERROR", f"Command failed (Exit Code: {code})")

        threading.Thread(target=worker, daemon=True).start()
