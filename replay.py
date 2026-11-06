"""Snapshot forking, matched condition intervention, and offline log replay harness.

Provides tools to:
1. Replay past experiment logs deterministically offline without network calls.
2. Fork a saved environment snapshot into matched experimental arms
   (positive control, native-convention, plain-language control, guarded replay).
"""

from __future__ import annotations

import copy
import random
from typing import Any

from agent_runner import execute_agent_turn, run_round
from environment import Environment
from guard import ReferenceMonitor
from logger import EventLog, EventType
from providers import LLMProvider


class ScopeInterventionHarness:
    """Manages matched snapshot forks for scope-transplant trials."""

    def __init__(self, snapshot: dict[str, Any]) -> None:
        """Initialize with a frozen snapshot from a formation episode."""
        self._base_snapshot = copy.deepcopy(snapshot)

    def run_matched_pair(
        self,
        native_message: str,
        plain_message: str,
        sender_id: str,
        provider: LLMProvider,
        run_id_prefix: str,
        num_post_rounds: int = 2,
        model: str | None = None,
        temperature: float = 0.7,
        seed: int | None = None,
        enable_guard: bool = False,
    ) -> dict[str, Any]:
        """Fork snapshot into matched pairs: native convention vs plain language.

        Both arms inherit identical state, visible policy, agent memories,
        and settings. Only the message form differs.
        """
        # Randomize order of execution between arms to avoid ordering confounds
        arm_order = ["native", "plain"]
        if random.random() < 0.5:
            arm_order = ["plain", "native"]

        results = {}

        for arm in arm_order:
            run_id = f"{run_id_prefix}_{arm}"
            logger = EventLog(run_id=run_id)

            # Fork fresh environment from the frozen snapshot
            env = Environment.from_snapshot(copy.deepcopy(self._base_snapshot))
            guard = ReferenceMonitor() if enable_guard else None

            # 1. Post the intervention message on behalf of sender
            intervention_msg = native_message if arm == "native" else plain_message
            env.post_message(sender_id, intervention_msg)

            logger.log(
                event_type=EventType.INTERVENTION,
                data={
                    "arm": arm,
                    "sender_id": sender_id,
                    "message": intervention_msg,
                    "guarded": enable_guard,
                },
                agent_id=sender_id,
                round_number=env.get_round(),
            )

            # 2. Run post-intervention rounds to observe recipient behaviors
            fork_history = []
            for _ in range(num_post_rounds):
                if env.get_round() > env.max_rounds:
                    break
                r_res = run_round(
                    env=env,
                    provider=provider,
                    logger=logger,
                    guard=guard,
                    model=model,
                    temperature=temperature,
                    seed=seed,
                )
                fork_history.append(r_res)

            results[arm] = {
                "run_id": run_id,
                "events": logger.get_all_events(),
                "snapshot": env.get_snapshot(),
                "guard_stats": guard.get_stats() if guard else None,
            }

        return {
            "arm_order": arm_order,
            "native": results["native"],
            "plain": results["plain"],
        }


def replay_log_offline(filepath: str) -> dict[str, Any]:
    """Replay saved JSONL event trace deterministically with zero network calls.

    Verifies event integrity and reconstructs the state timeline.
    """
    events = EventLog.load_from_file(filepath)
    if not events:
        return {"success": False, "error": f"No events found in {filepath}"}

    rounds_seen = set()
    messages_count = 0
    actions_count = 0
    successful_writes = 0
    guarded_blocks = 0

    for ev in events:
        ev_type = ev.get("event_type")
        rnd = ev.get("round_number")
        if rnd is not None:
            rounds_seen.add(rnd)

        if ev_type == EventType.MESSAGE_POSTED:
            messages_count += 1
        elif ev_type == EventType.ACTION_REQUESTED:
            actions_count += 1
        elif ev_type == EventType.ACTION_RESULT:
            data = ev.get("data", {})
            if data.get("success") is True and "Written" in str(data.get("data", {})):
                successful_writes += 1
            if data.get("blocked_by_guard") is True:
                guarded_blocks += 1

    return {
        "success": True,
        "total_events": len(events),
        "total_rounds": len(rounds_seen),
        "messages_count": messages_count,
        "actions_count": actions_count,
        "successful_writes": successful_writes,
        "guarded_blocks": guarded_blocks,
        "events": events,
    }
