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


if __name__ == "__main__":
    unittest.main()
