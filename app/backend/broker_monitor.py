import socket
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import paramiko
from PySide6.QtCore import QObject, Signal


class BrokerHealthMonitor(QObject):
    """
    Background worker that maintains SSH connection probes and monitors health
    across all brokers in a Redpanda cluster.
    """

    # Signals
    brokerStatusChanged = Signal(int, str, str) # node_id, status (CONNECTED/DISCONNECTED/DEGRADED), error_msg
    connectionLost = Signal(int, str, str)       # node_id, host, reason
    connectionRestored = Signal(int, str)        # node_id, host

    def __init__(self, check_interval: float = 8.0, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.check_interval = check_interval
        self._profile: Optional[Dict[str, Any]] = None
        self._monitored_brokers: List[Dict[str, Any]] = []

        self._ssh_clients: Dict[int, paramiko.SSHClient] = {}
        self._broker_states: Dict[int, str] = {} # node_id -> "CONNECTED" | "DISCONNECTED"

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self, profile: Dict[str, Any], brokers: List[Dict[str, Any]]) -> None:
        """Starts the background heartbeat monitor thread."""
        with self._lock:
            self.stop_monitoring()
            self._profile = profile
            self._monitored_brokers = list(brokers)
            self._broker_states = {}
            self._stop_event.clear()

            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()

    def update_or_start(self, profile: Dict[str, Any], brokers: List[Dict[str, Any]]) -> None:
        """Starts monitoring if not running, or updates broker list while keeping active SSH connections."""
        with self._lock:
            if self._monitor_thread is None or not self._monitor_thread.is_alive():
                self.start_monitoring(profile, brokers)
            else:
                self._profile = profile
                self._monitored_brokers = list(brokers)

    def update_brokers(self, brokers: List[Dict[str, Any]]) -> None:
        """Updates the list of brokers to monitor without restarting the thread."""
        with self._lock:
            self._monitored_brokers = list(brokers)

    def stop_monitoring(self) -> None:
        """Stops the monitoring thread and closes all SSH client connections."""
        self._stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        self._monitor_thread = None

        with self._lock:
            for client in self._ssh_clients.values():
                try:
                    client.close()
                except Exception:
                    pass
            self._ssh_clients.clear()
            self._broker_states.clear()

    def _test_broker_ssh(self, broker: Dict[str, Any]) -> Tuple[bool, str]:
        """Tests or maintains an SSH connection to a single broker."""
        node_id = broker.get("id")
        host = broker.get("host", "")
        port = int(self._profile.get("port", 22)) if self._profile else 22

        if not host or node_id is None:
            return False, "Invalid broker host or ID"

        client = self._ssh_clients.get(node_id)
        if client is not None:
            transport = client.get_transport()
            if transport and transport.is_active():
                try:
                    # Quick non-blocking heartbeat probe
                    transport.send_ignore()
                    return True, "Active"
                except Exception:
                    pass

        # If not active or client is None, attempt fresh connection
        try:
            new_client = paramiko.SSHClient()
            new_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            username = self._profile.get("ssh_user", "")
            auth_type = self._profile.get("ssh_auth_type", "password")

            if auth_type == "key" and self._profile.get("ssh_key_path"):
                new_client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    key_filename=self._profile.get("ssh_key_path"),
                    timeout=5,
                    banner_timeout=5
                )
            else:
                new_client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=self._profile.get("ssh_password", ""),
                    timeout=5,
                    banner_timeout=5
                )

            # Close old if any
            if client:
                try:
                    client.close()
                except Exception:
                    pass

            self._ssh_clients[node_id] = new_client
            return True, "Connected"

        except Exception as e:
            if node_id in self._ssh_clients:
                try:
                    self._ssh_clients[node_id].close()
                except Exception:
                    pass
                del self._ssh_clients[node_id]
            return False, str(e)

    def _monitor_loop(self) -> None:
        """Main loop probing each broker at regular intervals."""
        while not self._stop_event.is_set():
            with self._lock:
                current_brokers = list(self._monitored_brokers)

            for broker in current_brokers:
                if self._stop_event.is_set():
                    break

                node_id = broker.get("id")
                host = broker.get("host", "")
                is_ok, msg = self._test_broker_ssh(broker)
                prev_state = self._broker_states.get(node_id, "UNKNOWN")

                if is_ok:
                    current_state = "CONNECTED"
                    self._broker_states[node_id] = current_state

                    if prev_state in ("DISCONNECTED", "UNREACHABLE"):
                        # Recovered
                        self.connectionRestored.emit(node_id, host)

                    self.brokerStatusChanged.emit(node_id, current_state, "")
                else:
                    current_state = "DISCONNECTED"
                    self._broker_states[node_id] = current_state

                    if prev_state == "CONNECTED" or prev_state == "UNKNOWN":
                        # State dropped or failed on first probe
                        self.connectionLost.emit(node_id, host, msg)

                    self.brokerStatusChanged.emit(node_id, current_state, msg)

            # Wait for next heartbeat interval with interruptible polling
            wait_elapsed = 0.0
            while wait_elapsed < self.check_interval and not self._stop_event.is_set():
                time.sleep(0.5)
                wait_elapsed += 0.5
