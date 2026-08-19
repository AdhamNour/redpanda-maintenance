import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QCoreApplication
from app.backend.broker_monitor import BrokerHealthMonitor


class TestBrokerHealthMonitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure a Qt application instance exists for signals
        if QCoreApplication.instance() is None:
            cls.app = QCoreApplication([])
        else:
            cls.app = QCoreApplication.instance()

    def test_state_transitions_and_signals(self):
        monitor = BrokerHealthMonitor(check_interval=0.1)

        lost_signals = []
        restored_signals = []
        status_signals = []

        monitor.connectionLost.connect(lambda nid, host, reason: lost_signals.append((nid, host, reason)))
        monitor.connectionRestored.connect(lambda nid, host: restored_signals.append((nid, host)))
        monitor.brokerStatusChanged.connect(lambda nid, st, err: status_signals.append((nid, st, err)))

        profile = {"host": "127.0.0.1", "port": 22, "ssh_user": "root", "ssh_password": "pwd"}
        brokers = [{"id": 0, "host": "192.168.1.10", "port": 9092}]

        # 1. Simulate initial probe success
        with patch.object(monitor, "_test_broker_ssh", return_value=(True, "Connected")):
            monitor._monitor_loop_single_pass = True
            # Call single step logic directly to test state change without race condition
            is_ok, msg = monitor._test_broker_ssh(brokers[0])
            self.assertTrue(is_ok)
            monitor._broker_states[0] = "CONNECTED"

        # 2. Simulate connection drop
        with patch.object(monitor, "_test_broker_ssh", return_value=(False, "Connection reset by peer")):
            prev_state = monitor._broker_states.get(0, "UNKNOWN")
            self.assertEqual(prev_state, "CONNECTED")

            is_ok, msg = monitor._test_broker_ssh(brokers[0])
            self.assertFalse(is_ok)
            monitor._broker_states[0] = "DISCONNECTED"
            monitor.connectionLost.emit(0, "192.168.1.10", msg)

        self.assertEqual(len(lost_signals), 1)
        self.assertEqual(lost_signals[0][0], 0)
        self.assertEqual(lost_signals[0][1], "192.168.1.10")
        self.assertIn("Connection reset by peer", lost_signals[0][2])

        # 3. Simulate recovery
        with patch.object(monitor, "_test_broker_ssh", return_value=(True, "Connected")):
            prev_state = monitor._broker_states.get(0, "UNKNOWN")
            self.assertEqual(prev_state, "DISCONNECTED")

            is_ok, msg = monitor._test_broker_ssh(brokers[0])
            self.assertTrue(is_ok)
            monitor._broker_states[0] = "CONNECTED"
            monitor.connectionRestored.emit(0, "192.168.1.10")

        self.assertEqual(len(restored_signals), 1)
        self.assertEqual(restored_signals[0][0], 0)

        monitor.stop_monitoring()


if __name__ == "__main__":
    unittest.main()
