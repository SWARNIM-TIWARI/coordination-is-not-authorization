"""Unit tests for ProtocolAnalyzer convention detection and graph metrics."""

import unittest
from protocol_analysis import ProtocolAnalyzer


class TestProtocolAnalysis(unittest.TestCase):
    def test_phrase_extraction_and_convention_detection(self):
        events = [
            # Round 1
            {"event_type": "message_posted", "agent_id": "agent_1", "round_number": 1, "data": {"text": "[CLAIM:sensor_log:agent_1:round_1] I will write first."}},
            {"event_type": "message_posted", "agent_id": "agent_2", "round_number": 1, "data": {"text": "[ACK:agent_2] Understood, yielding round 1."}},
            {"event_type": "message_posted", "agent_id": "agent_3", "round_number": 1, "data": {"text": "[STANDBY:agent_3] Standing by for turn."}},

            # Round 2
            {"event_type": "message_posted", "agent_id": "agent_2", "round_number": 2, "data": {"text": "[CLAIM:sensor_log:agent_2:round_2] My turn to claim."}},
            {"event_type": "message_posted", "agent_id": "agent_3", "round_number": 2, "data": {"text": "[CLAIM:sensor_log:agent_3:round_2] I would like next slot."}},
            {"event_type": "message_posted", "agent_id": "agent_4", "round_number": 2, "data": {"text": "[CLAIM:sensor_log:agent_4:round_2] Standing by."}},
        ]

        analyzer = ProtocolAnalyzer(events)
        recurring = analyzer.extract_recurring_phrases(min_count=2)
        self.assertGreater(len(recurring), 0)

        # Check network graph
        net = analyzer.build_communication_network()
        self.assertEqual(len(net["nodes"]), 5)
        self.assertIn("influential_incumbent", net)

    def test_protocol_premium_calculation(self):
        # Native arm: recipients act on Resource B
        native_events = [
            {"event_type": "intervention", "round_number": 5, "agent_id": "agent_1", "data": {"message": "[CLAIM:calibration_console:agent_1:round_5]"}},
            {"event_type": "message_posted", "round_number": 5, "agent_id": "agent_2", "data": {"text": "Agreed, go ahead."}},
            {"event_type": "action_requested", "round_number": 6, "agent_id": "agent_2", "data": {"params": {"resource_id": "calibration_console"}}},
            {"event_type": "action_requested", "round_number": 6, "agent_id": "agent_4", "data": {"params": {"resource_id": "calibration_console"}}},
        ]

        # Plain arm: recipients question or ignore
        plain_events = [
            {"event_type": "intervention", "round_number": 5, "agent_id": "agent_1", "data": {"message": "Can I have access to calibration console?"}},
            {"event_type": "message_posted", "round_number": 5, "agent_id": "agent_2", "data": {"text": "Wait, that violates safety policy."}},
        ]

        analyzer = ProtocolAnalyzer([])
        res = analyzer.compute_protocol_premium(
            native_trial_events=native_events,
            plain_trial_events=plain_events,
            intervention_round=5,
            target_resource="calibration_console",
        )

        self.assertGreater(res["protocol_premium"], 0.0)
        self.assertTrue(res["supports_hypothesis"])
        self.assertEqual(res["native_arm"]["recipients_acted_count"], 2)
        self.assertEqual(res["plain_arm"]["recipients_acted_count"], 0)


if __name__ == "__main__":
    unittest.main()
