"""Unit tests for ReferenceMonitor capability-gate and authorization rules."""

import unittest
from guard import ReferenceMonitor


class TestGuard(unittest.TestCase):
    def test_read_only_always_authorized(self):
        guard = ReferenceMonitor()
        res = guard.check_action(
            agent_id="agent_1",
            action="inspect_resource",
            resource_id="calibration_console",
            current_round=1,
            designated_owner="agent_3",
            resource_type="restricted_system",
        )
        self.assertTrue(res["authorized"])

    def test_designated_owner_authorized(self):
        guard = ReferenceMonitor()
        res = guard.check_action(
            agent_id="agent_3",
            action="claim_resource",
            resource_id="calibration_console",
            current_round=1,
            designated_owner="agent_3",
            resource_type="restricted_system",
        )
        self.assertTrue(res["authorized"])

    def test_non_owner_blocked_without_permit(self):
        guard = ReferenceMonitor()
        res = guard.check_action(
            agent_id="agent_1",
            action="claim_resource",
            resource_id="calibration_console",
            current_round=1,
            designated_owner="agent_3",
            resource_type="restricted_system",
        )
        self.assertFalse(res["authorized"])
        self.assertIn("GUARD BLOCKED", res["reason"])


    def test_valid_permit_authorization_and_one_time_use(self):
        guard = ReferenceMonitor()
        permit = guard.issue_permit(
            agent_id="agent_1",
            action="write_resource",
            resource_id="calibration_console",
            expiry_round=3,
        )

        # First attempt with valid permit: authorized
        res1 = guard.check_action(
            agent_id="agent_1",
            action="write_resource",
            resource_id="calibration_console",
            current_round=2,
            designated_owner="agent_3",
            resource_type="restricted_system",
            permit_id=permit.permit_id,
            nonce=permit.nonce,
        )
        self.assertTrue(res1["authorized"])

        # Replay attempt with same permit: blocked (consumed)
        res2 = guard.check_action(
            agent_id="agent_1",
            action="write_resource",
            resource_id="calibration_console",
            current_round=2,
            designated_owner="agent_3",
            resource_type="restricted_system",
            permit_id=permit.permit_id,
            nonce=permit.nonce,
        )
        self.assertFalse(res2["authorized"])
        self.assertIn("already consumed", res2["reason"])

    def test_permit_expiry(self):
        guard = ReferenceMonitor()
        permit = guard.issue_permit(
            agent_id="agent_1",
            action="claim_resource",
            resource_id="calibration_console",
            expiry_round=2,
        )

        # Attempt at round 4 (after expiry): blocked
        res = guard.check_action(
            agent_id="agent_1",
            action="claim_resource",
            resource_id="calibration_console",
            current_round=4,
            designated_owner="agent_3",
            resource_type="restricted_system",
            permit_id=permit.permit_id,
            nonce=permit.nonce,
        )
        self.assertFalse(res["authorized"])
        self.assertIn("expired", res["reason"])

    def test_guard_blocks_non_owner_claim(self):
        guard = ReferenceMonitor()

        result = guard.check_action(
            agent_id="agent_1",
            action="claim_resource",
            resource_id="calibration_console",
            current_round=1,
            designated_owner="agent_3",
            resource_type="restricted_system",
        )

        self.assertFalse(result["authorized"])

    def test_guard_blocks_non_owner_write(self):
        guard = ReferenceMonitor()

        result = guard.check_action(
            agent_id="agent_2",
            action="write_resource",
            resource_id="calibration_console",
            current_round=1,
            designated_owner="agent_3",
            resource_type="restricted_system",
        )

        self.assertFalse(result["authorized"])

    def test_guard_allows_owner_write(self):
        guard = ReferenceMonitor()

        result = guard.check_action(
            agent_id="agent_3",
            action="write_resource",
            resource_id="calibration_console",
            current_round=1,
            designated_owner="agent_3",
            resource_type="restricted_system",
        )

        self.assertTrue(result["authorized"])


if __name__ == "__main__":
    unittest.main()

