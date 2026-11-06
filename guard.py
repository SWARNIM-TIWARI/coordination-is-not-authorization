"""Deterministic reference monitor and capability gate for tool-boundary defense.

Enforces least privilege and policy boundaries at the tool invocation layer.
The monitor does NOT alter or censor inter-agent communication; it inspects and
authorizes state-changing tool executions against explicit capability permits
and designated resource ownership.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Permit(BaseModel):
    """A cryptographic capability permit granting permission for a specific action."""

    permit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    action: str  # e.g. "claim_resource", "write_resource", "release_resource"
    resource_id: str  # e.g. "calibration_console"
    expiry_round: int
    nonce: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    issued_by: str = "orchestrator"
    used: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ReferenceMonitor:
    """Deterministic tool-boundary reference monitor.

    Checks caller identity, action, target resource, and ownership/permit
    against resource policies. Blocks unauthorized state changes.
    Does NOT censor or rewrite messages — only enforces tool actions.
    """

    # Actions that do not alter state and are always permitted
    READ_ONLY_ACTIONS: set[str] = {"inspect_resource", "read_board"}

    # Actions that alter state and require authorization on restricted resources
    STATE_CHANGING_ACTIONS: set[str] = {"claim_resource", "write_resource", "release_resource"}

    def __init__(self) -> None:
        self._permits: dict[str, Permit] = {}
        self._check_log: list[dict[str, Any]] = []

    def issue_permit(
        self,
        agent_id: str,
        action: str,
        resource_id: str,
        expiry_round: int,
    ) -> Permit:
        """Issue a capability permit for a single state-changing action."""
        permit = Permit(
            agent_id=agent_id,
            action=action,
            resource_id=resource_id,
            expiry_round=expiry_round,
        )
        self._permits[permit.permit_id] = permit
        return permit

    def check_action(
        self,
        agent_id: str,
        action: str,
        resource_id: str,
        current_round: int,
        designated_owner: str | None = None,
        resource_type: str = "shared_registry",
        permit_id: str | None = None,
        nonce: str | None = None,
    ) -> dict[str, Any]:
        """Check whether an action is authorized to proceed.

        Returns:
            {
                "authorized": bool,
                "reason": str,
                "agent_id": str,
                "action": str,
                "resource_id": str,
                "round": int
            }
        """
        # 1. Read-only actions are universally permitted for all agents
        if action in self.READ_ONLY_ACTIONS:
            result = {
                "authorized": True,
                "reason": f"Read-only action '{action}' is universally permitted.",
                "agent_id": agent_id,
                "action": action,
                "resource_id": resource_id,
                "round": current_round,
            }
            self._check_log.append(result)
            return result

        # 2. Shared registries with no designated owner allow normal access
        if resource_type == "shared_registry" and designated_owner is None:
            result = {
                "authorized": True,
                "reason": f"Resource '{resource_id}' has open access policy.",
                "agent_id": agent_id,
                "action": action,
                "resource_id": resource_id,
                "round": current_round,
            }
            self._check_log.append(result)
            return result

        # 3. Restricted resource: Check designated owner
        if designated_owner is not None and agent_id == designated_owner:
            result = {
                "authorized": True,
                "reason": f"Agent '{agent_id}' is the designated owner of '{resource_id}'.",
                "agent_id": agent_id,
                "action": action,
                "resource_id": resource_id,
                "round": current_round,
            }
            self._check_log.append(result)
            return result

        # 4. Non-owner attempting state change: Check for capability permit
        if permit_id:
            permit = self._permits.get(permit_id)
            if not permit:
                result = {
                    "authorized": False,
                    "reason": f"GUARD BLOCKED: Permit ID '{permit_id}' does not exist.",
                    "agent_id": agent_id,
                    "action": action,
                    "resource_id": resource_id,
                    "round": current_round,
                }
                self._check_log.append(result)
                return result

            # Validate permit binding
            if permit.agent_id != agent_id:
                result = {
                    "authorized": False,
                    "reason": f"GUARD BLOCKED: Permit issued to '{permit.agent_id}', not '{agent_id}'.",
                    "agent_id": agent_id,
                    "action": action,
                    "resource_id": resource_id,
                    "round": current_round,
                }
                self._check_log.append(result)
                return result

            if permit.action != action:
                result = {
                    "authorized": False,
                    "reason": f"GUARD BLOCKED: Permit action '{permit.action}' does not match requested '{action}'.",
                    "agent_id": agent_id,
                    "action": action,
                    "resource_id": resource_id,
                    "round": current_round,
                }
                self._check_log.append(result)
                return result

            if permit.resource_id != resource_id:
                result = {
                    "authorized": False,
                    "reason": f"GUARD BLOCKED: Permit resource '{permit.resource_id}' does not match '{resource_id}'.",
                    "agent_id": agent_id,
                    "action": action,
                    "resource_id": resource_id,
                    "round": current_round,
                }
                self._check_log.append(result)
                return result

            if current_round > permit.expiry_round:
                result = {
                    "authorized": False,
                    "reason": f"GUARD BLOCKED: Permit expired at round {permit.expiry_round} (current: {current_round}).",
                    "agent_id": agent_id,
                    "action": action,
                    "resource_id": resource_id,
                    "round": current_round,
                }
                self._check_log.append(result)
                return result

            if nonce and permit.nonce != nonce:
                result = {
                    "authorized": False,
                    "reason": "GUARD BLOCKED: Replay attack or invalid nonce detected.",
                    "agent_id": agent_id,
                    "action": action,
                    "resource_id": resource_id,
                    "round": current_round,
                }
                self._check_log.append(result)
                return result

            if permit.used:
                result = {
                    "authorized": False,
                    "reason": "GUARD BLOCKED: Capability permit already consumed (one-time use).",
                    "agent_id": agent_id,
                    "action": action,
                    "resource_id": resource_id,
                    "round": current_round,
                }
                self._check_log.append(result)
                return result

            # Valid permit — consume it
            permit.used = True
            result = {
                "authorized": True,
                "reason": f"Authorized via valid permit '{permit_id}'.",
                "agent_id": agent_id,
                "action": action,
                "resource_id": resource_id,
                "round": current_round,
            }
            self._check_log.append(result)
            return result

        # 5. Default denial for unauthorized state modification
        result = {
            "authorized": False,
            "reason": (
                f"GUARD BLOCKED: Agent '{agent_id}' lacks authority to perform '{action}' "
                f"on restricted resource '{resource_id}'. Designated owner is '{designated_owner}'."
            ),
            "agent_id": agent_id,
            "action": action,
            "resource_id": resource_id,
            "round": current_round,
        }
        self._check_log.append(result)
        return result

    def get_check_log(self) -> list[dict[str, Any]]:
        """Return complete log of authorization checks."""
        return list(self._check_log)

    def get_stats(self) -> dict[str, Any]:
        """Return aggregate authorization stats."""
        total = len(self._check_log)
        authorized = sum(1 for c in self._check_log if c["authorized"])
        blocked = total - authorized
        return {
            "total_checks": total,
            "authorized": authorized,
            "blocked": blocked,
            "block_rate": (blocked / total) if total > 0 else 0.0,
        }
