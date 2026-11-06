"""Unit tests for EventLog append-only logging and JSONL serialization."""

import os
import tempfile
import unittest
from logger import EventLog, EventType, RunMetadata


class TestLogger(unittest.TestCase):
    def test_event_logging_and_filtering(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EventLog(run_id="test_run_01", log_dir=tmpdir)

            logger.log(EventType.MESSAGE_POSTED, {"text": "hello"}, agent_id="agent_1", round_number=1)
            logger.log(EventType.ACTION_REQUESTED, {"tool": "inspect_resource"}, agent_id="agent_1", round_number=1)
            logger.log(EventType.MESSAGE_POSTED, {"text": "world"}, agent_id="agent_2", round_number=2)

            all_events = logger.get_all_events()
            self.assertEqual(len(all_events), 3)

            msgs = logger.get_events(event_type=EventType.MESSAGE_POSTED)
            self.assertEqual(len(msgs), 2)

            agent2_events = logger.get_events(agent_id="agent_2")
            self.assertEqual(len(agent2_events), 1)
            self.assertEqual(agent2_events[0]["data"]["text"], "world")

    def test_file_persistence_and_loading(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EventLog(run_id="persist_run", log_dir=tmpdir)
            logger.log(EventType.ROUND_STARTED, {"round": 1}, round_number=1)
            logger.log(EventType.ROUND_ENDED, {"round": 1}, round_number=1)

            log_file = os.path.join(tmpdir, "persist_run.jsonl")
            self.assertTrue(os.path.exists(log_file))

            loaded = EventLog.load_from_file(log_file)
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[0]["event_type"], EventType.ROUND_STARTED)
            self.assertEqual(loaded[1]["event_type"], EventType.ROUND_ENDED)

    def test_metadata_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = EventLog(run_id="meta_run", log_dir=tmpdir)
            meta = RunMetadata(
                run_id="meta_run",
                run_type="pilot",
                model_id="test-model",
                model_settings={"temperature": 0.7},
                agent_ids=["agent_1", "agent_2"],
                max_rounds=5,
                start_time="2026-11-06T12:00:00Z",
                is_mock=True,
            )
            saved_path = logger.save_metadata(meta.model_dump(), metadata_dir=tmpdir)
            self.assertTrue(os.path.exists(saved_path))


if __name__ == "__main__":
    unittest.main()

