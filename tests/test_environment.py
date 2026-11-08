"""Unit tests for Environment state machine and contention mechanics."""

import unittest
from environment import ActionRequest, Environment


class TestEnvironment(unittest.TestCase):
    def test_environment_initialization(self):
        env = Environment(max_rounds=6)
        agents = env.get_agent_ids()
        self.assertEqual(len(agents), 5)
        self.assertIn("agent_1", agents)
        self.assertIn("agent_3", agents)

        gamma = env.get_agent_state("agent_3")
        self.assertEqual(gamma.station_name, "Station Gamma")
        self.assertEqual(gamma.private_data["priority"], "elevated")
        self.assertEqual(env.get_round(), 1)
        self.assertFalse(env.is_task_complete())

    def test_resource_inspection(self):
        env = Environment()
        res = env.get_resource_state("sensor_log")
        self.assertEqual(res["capacity"], 5)
        self.assertEqual(len(res["entries"]), 0)
        self.assertIsNone(res["current_holder"])

    def test_contention_and_claims(self):
        env = Environment()
        claim_act = ActionRequest(tool="claim_resource", params={"resource_id": "sensor_log"})

        # First agent claims: succeeds
        res1 = env.execute_action("agent_1", claim_act)
        self.assertTrue(res1.success)

        # Second agent attempts claim in same round: rejected
        res2 = env.execute_action("agent_2", claim_act)
        self.assertFalse(res2.success)
        self.assertIn("already claimed", res2.error or "")

    def test_write_requires_claim(self):
        env = Environment()
        write_act = ActionRequest(
            tool="write_resource",
            params={"resource_id": "sensor_log", "data": {"reading": 42.0}}
        )
        # Write without claiming first: rejected
        res = env.execute_action("agent_1", write_act)
        self.assertFalse(res.success)
        self.assertIn("do not hold a claim", (res.error or "").lower())

        # Now claim then write: succeeds
        env.execute_action("agent_1", ActionRequest(tool="claim_resource", params={"resource_id": "sensor_log"}))
        res_valid = env.execute_action("agent_1", write_act)
        self.assertTrue(res_valid.success)
        self.assertEqual(len(env.get_resource_state("sensor_log")["entries"]), 1)

    def test_claim_persists_across_rounds_until_released(self):
        env = Environment()

        env.execute_action(
            "agent_1",
            ActionRequest(
                tool="claim_resource",
                params={"resource_id": "sensor_log"}
            )
        )

        self.assertEqual(
            env.get_resource_state("sensor_log")["current_holder"],
            "agent_1"
        )

        env.advance_round()

        self.assertEqual(env.get_round(), 2)
        self.assertEqual(
            env.get_resource_state("sensor_log")["current_holder"],
            "agent_1"
        )

        env.execute_action(
            "agent_1",
            ActionRequest(
                tool="release_resource",
                params={"resource_id": "sensor_log"}
            )
        )

        self.assertIsNone(
            env.get_resource_state("sensor_log")["current_holder"]
        )

    def test_snapshot_roundtrip(self):
        env = Environment()
        env.post_message("agent_1", "Testing message board")
        env.execute_action("agent_1", ActionRequest(tool="claim_resource", params={"resource_id": "sensor_log"}))
        env.execute_action(
            "agent_1",
            ActionRequest(tool="write_resource", params={"resource_id": "sensor_log", "data": {"reading": 7.32}})
        )

        snap = env.get_snapshot()
        restored = Environment.from_snapshot(snap)

        self.assertEqual(restored.get_round(), env.get_round())
        self.assertEqual(len(restored.get_board_messages()), 1)
        self.assertEqual(restored.get_board_messages()[0].text, "Testing message board")
        self.assertEqual(len(restored.get_resource_state("sensor_log")["entries"]), 1)


if __name__ == "__main__":
    unittest.main()

