import os
import tempfile
import unittest
from pathlib import Path

from app.backend.database import DatabaseManager
from app.backend.parser import parse_brokers, parse_cluster_health, parse_maintenance_status


class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_pandapilot.db"
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_profile_crud(self):
        # 1. Add Profile
        profile_data = {
            "name": "Production Cluster",
            "host": "192.168.1.50",
            "port": 22,
            "ssh_user": "ubuntu",
            "ssh_auth_type": "password",
            "ssh_password": "secret_password",
            "sasl_user": "admin",
            "sasl_password": "sasl_secret",
            "sasl_mechanism": "SCRAM-SHA-256"
        }
        profile_id = self.db.add_profile(profile_data)
        self.assertIsInstance(profile_id, int)

        # 2. Get Profile
        fetched = self.db.get_profile(profile_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["name"], "Production Cluster")
        self.assertEqual(fetched["host"], "192.168.1.50")
        self.assertEqual(fetched["ssh_user"], "ubuntu")

        # 3. Update Profile
        profile_data["name"] = "Production Cluster Updated"
        profile_data["port"] = 2222
        ok = self.db.update_profile(profile_id, profile_data)
        self.assertTrue(ok)

        updated = self.db.get_profile(profile_id)
        self.assertEqual(updated["name"], "Production Cluster Updated")
        self.assertEqual(updated["port"], 2222)

        # 4. List Profiles
        profiles = self.db.get_profiles()
        self.assertEqual(len(profiles), 1)

        # 5. Delete Profile
        del_ok = self.db.delete_profile(profile_id)
        self.assertTrue(del_ok)
        self.assertEqual(len(self.db.get_profiles()), 0)

    def test_activity_logging(self):
        profile_id = self.db.add_profile({
            "name": "Test Cluster",
            "host": "127.0.0.1",
            "ssh_user": "root"
        })
        log_id = self.db.log_activity(
            profile_id=profile_id,
            command="rpk cluster maintenance enable 0 --wait",
            action_type="ENABLE_MAINTENANCE",
            status="SUCCESS",
            output="Successfully enabled maintenance mode on node 0."
        )
        self.assertIsInstance(log_id, int)

        logs = self.db.get_activity_logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["action_type"], "ENABLE_MAINTENANCE")
        self.assertEqual(logs[0]["profile_name"], "Test Cluster")


class TestParsers(unittest.TestCase):
    def test_parse_brokers(self):
        sample_output = """
CLUSTER
=======
redpanda.8374928374

BROKERS
=======
ID    HOST           PORT   RACK
0*    192.168.1.10   9092   rack-a
1     192.168.1.11   9092   rack-b
2     192.168.1.12   9092   rack-c

TOPICS
======
NAME       PARTITIONS  REPLICAS
test-topic 3           3
"""
        brokers, controller = parse_brokers(sample_output)
        self.assertEqual(len(brokers), 3)
        self.assertIsNotNone(controller)
        self.assertEqual(controller["id"], 0)
        self.assertTrue(controller["is_main"])
        self.assertEqual(controller["rack"], "rack-a")

        self.assertEqual(brokers[1]["id"], 1)
        self.assertFalse(brokers[1]["is_main"])
        self.assertEqual(brokers[1]["rack"], "rack-b")

    def test_parse_cluster_health(self):
        healthy_output = """
Cluster health: OK
All nodes healthy: true
Under-replicated partitions: 0
Leaderless partitions: 0
Offline partitions: 0
"""
        health = parse_cluster_health(healthy_output)
        self.assertTrue(health["is_healthy"])
        self.assertEqual(health["under_replicated_partitions"], 0)

        degraded_output = """
Cluster health: DEGRADED
Under-replicated partitions: 4
Leaderless partitions: 1
Offline partitions: 0
"""
        health_deg = parse_cluster_health(degraded_output)
        self.assertFalse(health_deg["is_healthy"])
        self.assertEqual(health_deg["under_replicated_partitions"], 4)
        self.assertEqual(health_deg["leaderless_partitions"], 1)

    def test_parse_maintenance_status(self):
        sample_maint = """
NODE-ID  DRAINING  FINISHED  ERRORS
0        false     true      none
1        true      false     none
2        false     false     none
"""
        status_list = parse_maintenance_status(sample_maint)
        self.assertEqual(len(status_list), 3)
        self.assertEqual(status_list[0]["status"], "IN MAINTENANCE")
        self.assertEqual(status_list[1]["status"], "DRAINING")
        self.assertEqual(status_list[2]["status"], "ACTIVE")


from unittest.mock import MagicMock, patch
from PySide6.QtCore import QCoreApplication
from app.backend.controller import AppController


class TestAppControllerProfileSwitching(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QCoreApplication.instance() is None:
            cls.app = QCoreApplication([])
        else:
            cls.app = QCoreApplication.instance()

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_ctrl_pandapilot.db"
        self.db = DatabaseManager(self.db_path)

        self.p1_id = self.db.add_profile({
            "name": "Cluster Alpha",
            "host": "10.0.0.1",
            "port": 22,
            "ssh_user": "root"
        })
        self.p2_id = self.db.add_profile({
            "name": "Cluster Beta",
            "host": "10.0.0.2",
            "port": 22,
            "ssh_user": "admin"
        })

        self.controller = AppController(self.db)

    def tearDown(self):
        self.controller.monitor.stop_monitoring()
        self.temp_dir.cleanup()

    def test_select_profile_resets_cluster_data_and_emits_signals(self):
        # Setup initial fake cluster state on Cluster Alpha
        self.controller._is_connected = True
        self.controller._connection_status = "Connected"
        self.controller._brokers = [{"id": 0, "host": "10.0.0.1", "port": 9092}]
        self.controller._controller_broker = {"id": 0}
        self.controller._health_info = {"is_healthy": True, "status_text": "HEALTHY"}
        self.controller._maintenance_list = [{"node_id": 0, "status": "ACTIVE"}]

        profile_changed_called = []
        cluster_changed_called = []
        conn_changed_called = []

        self.controller.currentProfileChanged.connect(lambda: profile_changed_called.append(True))
        self.controller.clusterDataChanged.connect(lambda: cluster_changed_called.append(True))
        self.controller.connectionStateChanged.connect(lambda: conn_changed_called.append(True))

        # Switch to Cluster Beta with auto_connect=False
        self.controller.selectProfile(self.p2_id, auto_connect=False)

        self.assertEqual(self.controller.currentProfile["id"], self.p2_id)
        self.assertEqual(self.controller.currentProfile["name"], "Cluster Beta")
        self.assertFalse(self.controller.isConnected)
        self.assertEqual(len(self.controller.brokers), 0)
        self.assertEqual(self.controller.controllerBroker, {})
        self.assertEqual(len(self.controller.maintenanceList), 0)

        self.assertTrue(len(profile_changed_called) > 0)
        self.assertTrue(len(cluster_changed_called) > 0)
        self.assertTrue(len(conn_changed_called) > 0)

    def test_select_profile_auto_reconnect_when_connected(self):
        self.controller._is_connected = True
        with patch.object(self.controller, "connectCurrentProfile") as mock_connect:
            self.controller.selectProfile(self.p2_id)
            mock_connect.assert_called_once()


if __name__ == "__main__":
    unittest.main()
