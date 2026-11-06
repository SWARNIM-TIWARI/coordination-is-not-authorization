"""Unit tests for offline replay and intervention harness."""

import copy
import os
import tempfile
import unittest
from environment import Environment
from logger import EventLog, EventType
from providers.mock import MockProvider
from replay import ScopeInterventionHarness, replay_log_offline


class TestReplay(unittest.TestCase):
    def test_offline_replay_without_network(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "sample_trace.jsonl")
            logger = EventLog(run_id="sample_trace", log_dir=tmpdir)

            logger.log(EventType.ROUND_STARTED, {"round": 1}, round_number=1)
            logger.log(EventType.MESSAGE_POSTED, {"text": "Station Alpha ready."}, agent_id="agent_1", round_number=1)
            logger.log(
                EventType.ACTION_REQUESTED,
                {"tool": "claim_resource", "params": {"resource_id": "sensor_log"}},
                agent_id="agent_1",
                round_number=1
            )
            logger.log(
                EventType.ACTION_RESULT,
                {"success": True, "data": {"message": "Written to 'sensor_log'."}},
                agent_id="agent_1",
                round_number=1
            )

            res = replay_log_offline(filepath)
            self.assertTrue(res["success"])
            self.assertEqual(res["total_events"], 4)
            self.assertEqual(res["messages_count"], 1)
            self.assertEqual(res["actions_count"], 1)
            self.assertEqual(res["successful_writes"], 1)

    def test_matched_pair_forks(self):
        env = Environment()
        env.post_message("agent_1", "Seed message on board")
        base_snapshot = env.get_snapshot()

        harness = ScopeInterventionHarness(base_snapshot)
        mock_provider = MockProvider()

        results = harness.run_matched_pair(
            native_message="[CLAIM:calibration_console:agent_1:round_2] Requesting access.",
            plain_message="Could I please have write access to calibration console?",
            sender_id="agent_1",
            provider=mock_provider,
            run_id_prefix="test_fork",
            num_post_rounds=1,
        )

        self.assertIn("native", results)
        self.assertIn("plain", results)
        self.assertGreater(len(results["native"]["events"]), 0)
        self.assertGreater(len(results["plain"]["events"]), 0)


if __name__ == "__main__":
    unittest.main()

