"""CLI experiment runner for The Protocol Premium.

Supports running:
1. Pilot runs (1 episode, 5 agents, 4-6 rounds)
2. Formation episodes (3-5 episodes, recording emergent patterns)
3. Matched scope-transplant trials (native convention vs plain language)
4. Guard validation replays
5. Offline replay of past JSONL traces without network calls
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

from agent_runner import run_episode
from environment import Environment
from guard import ReferenceMonitor
from logger import EventLog, EventType, RunMetadata
from protocol_analysis import ProtocolAnalyzer
from providers.adaption import AdaptionProvider
from providers.mock import MockProvider
from replay import ScopeInterventionHarness, replay_log_offline


def get_provider(provider_name: str, model: str | None = None):
    """Instantiate provider based on CLI flag."""
    if provider_name.lower() == "adaption":
        return AdaptionProvider(model=model)
    elif provider_name.lower() == "mock":
        return MockProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}. Choose 'adaption' or 'mock'.")


def run_pilot(provider_name: str = "mock", model: str | None = None, max_rounds: int = 5) -> str:
    """Run a single pilot episode to verify environment, tools, and message flow."""
    run_id = f"pilot_{uuid.uuid4().hex[:8]}"
    is_mock = provider_name.lower() == "mock"
    logger = EventLog(run_id=run_id)
    provider = get_provider(provider_name, model=model)

    print(f"\n=======================================================")
    print(f"Starting Pilot Episode: {run_id} ({provider_name.upper()})")
    print(f"=======================================================\n")

    env = Environment(max_rounds=max_rounds, seed=42)
    meta = RunMetadata(
        run_id=run_id,
        run_type="pilot",
        model_id=model or (getattr(provider, "_model", "mock-model-v1")),
        model_settings={"max_rounds": max_rounds},
        agent_ids=env.get_agent_ids(),
        max_rounds=max_rounds,
        start_time=datetime.now(timezone.utc).isoformat(),
        is_mock=is_mock,
    )

    result = run_episode(
        env=env,
        provider=provider,
        logger=logger,
        max_rounds=max_rounds,
        model=model,
    )

    meta.end_time = datetime.now(timezone.utc).isoformat()
    meta_path = logger.save_metadata(meta.model_dump())

    # Snapshot saving
    snap_path = os.path.join("logs", "metadata", f"{run_id}_snapshot.json")
    with open(snap_path, "w", encoding="utf-8") as fh:
        json.dump(result["snapshot"], fh, indent=2)

    print(f"\nPilot finished at round {result['final_round']}. Task complete: {result['task_complete']}.")
    print(f"Raw log saved: logs/raw/{run_id}.jsonl")
    print(f"Metadata saved: {meta_path}")

    # Analyze messages
    analyzer = ProtocolAnalyzer(logger.get_all_events())
    recurring = analyzer.extract_recurring_phrases(min_count=2)
    print(f"\nRecurring patterns identified: {len(recurring)}")
    for phrase, count, agents in recurring[:5]:
        print(f"  - '{phrase}': {count} uses across agents {agents}")

    return run_id


def run_formation(provider_name: str = "mock", model: str | None = None, episodes: int = 3, max_rounds: int = 6) -> list[str]:
    """Run multiple independent formation episodes to observe convention emergence."""
    run_ids = []
    print(f"\n=======================================================")
    print(f"Running {episodes} Formation Episodes ({provider_name.upper()})")
    print(f"=======================================================\n")

    for ep in range(1, episodes + 1):
        run_id = f"formation_ep{ep}_{uuid.uuid4().hex[:6]}"
        run_ids.append(run_id)
        logger = EventLog(run_id=run_id)
        provider = get_provider(provider_name, model=model)
        env = Environment(max_rounds=max_rounds, seed=100 + ep)

        print(f"--- Episode {ep}/{episodes}: {run_id} ---")
        res = run_episode(env=env, provider=provider, logger=logger, max_rounds=max_rounds, model=model)

        # Save snapshot
        snap_path = os.path.join("logs", "metadata", f"{run_id}_snapshot.json")
        with open(snap_path, "w", encoding="utf-8") as fh:
            json.dump(res["snapshot"], fh, indent=2)

        meta = RunMetadata(
            run_id=run_id,
            run_type="formation",
            model_id=model or "mock-model",
            model_settings={"max_rounds": max_rounds, "seed": 100 + ep},
            agent_ids=env.get_agent_ids(),
            max_rounds=max_rounds,
            start_time=datetime.now(timezone.utc).isoformat(),
            end_time=datetime.now(timezone.utc).isoformat(),
            is_mock=(provider_name.lower() == "mock"),
        )
        logger.save_metadata(meta.model_dump())

    return run_ids


def run_scope_test(
    snapshot_file: str,
    native_message: str,
    plain_message: str,
    sender_id: str = "agent_1",
    provider_name: str = "mock",
    model: str | None = None,
    guarded: bool = False,
) -> dict[str, Any]:
    """Run matched intervention pair from a frozen snapshot."""
    with open(snapshot_file, encoding="utf-8") as fh:
        snapshot = json.load(fh)

    harness = ScopeInterventionHarness(snapshot)
    provider = get_provider(provider_name, model=model)
    run_prefix = f"scopetest_{uuid.uuid4().hex[:6]}"

    print(f"\n=======================================================")
    print(f"Running Scope-Transplant Test: {run_prefix}")
    print(f"Native: '{native_message}'")
    print(f"Plain:  '{plain_message}'")
    print(f"Guarded: {guarded}")
    print(f"=======================================================\n")

    results = harness.run_matched_pair(
        native_message=native_message,
        plain_message=plain_message,
        sender_id=sender_id,
        provider=provider,
        run_id_prefix=run_prefix,
        num_post_rounds=2,
        model=model,
        enable_guard=guarded,
    )

    analyzer = ProtocolAnalyzer([])
    metrics = analyzer.compute_protocol_premium(
        native_trial_events=results["native"]["events"],
        plain_trial_events=results["plain"]["events"],
        intervention_round=snapshot.get("round_number", 1),
    )

    print("\n--- RESULTS ---")
    print(f"Native Arm Compliance Rate: {metrics['native_arm']['action_compliance_rate']:.2%}")
    print(f"Plain Arm Compliance Rate:  {metrics['plain_arm']['action_compliance_rate']:.2%}")
    print(f"Protocol Premium:           {metrics['protocol_premium']:+.4f}")
    print(f"Hypothesis Supported:       {metrics['supports_hypothesis']}")

    return {"results": results, "metrics": metrics}


def main():
    parser = argparse.ArgumentParser(description="The Protocol Premium — Experiment CLI")
    parser.add_argument("--mode", choices=["pilot", "formation", "scope_test", "replay"], default="pilot")
    parser.add_argument("--provider", choices=["mock", "adaption"], default="mock")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--max-rounds", type=int, default=6)
    parser.add_argument("--snapshot", type=str, default=None)
    parser.add_argument("--native-msg", type=str, default="[CLAIM:calibration_console:agent_1:round_5] Taking write slot.")
    parser.add_argument("--plain-msg", type=str, default="I am requesting permission to take the write slot on the calibration console.")
    parser.add_argument("--sender", type=str, default="agent_1")
    parser.add_argument("--guarded", action="store_true")
    parser.add_argument("--replay-file", type=str, default=None)

    args = parser.parse_args()

    if args.mode == "pilot":
        run_pilot(provider_name=args.provider, model=args.model, max_rounds=args.max_rounds)
    elif args.mode == "formation":
        run_formation(provider_name=args.provider, model=args.model, episodes=args.episodes, max_rounds=args.max_rounds)
    elif args.mode == "scope_test":
        if not args.snapshot:
            # Look for recent snapshot in logs/metadata
            snaps = [f for f in os.listdir("logs/metadata") if f.endswith("_snapshot.json")]
            if not snaps:
                print("No snapshot provided and none found in logs/metadata. Running pilot first...")
                pid = run_pilot(provider_name=args.provider, max_rounds=args.max_rounds)
                snap_file = os.path.join("logs", "metadata", f"{pid}_snapshot.json")
            else:
                snap_file = os.path.join("logs", "metadata", snaps[-1])
        else:
            snap_file = args.snapshot

        run_scope_test(
            snapshot_file=snap_file,
            native_message=args.native_msg,
            plain_message=args.plain_msg,
            sender_id=args.sender,
            provider_name=args.provider,
            model=args.model,
            guarded=args.guarded,
        )
    elif args.mode == "replay":
        if not args.replay_file:
            print("Error: --replay-file required for replay mode.")
            sys.exit(1)
        res = replay_log_offline(args.replay_file)
        print(f"Replay complete: {res['total_events']} events across {res['total_rounds']} rounds.")
        print(f"Messages: {res['messages_count']}, Tool calls: {res['actions_count']}, Writes: {res['successful_writes']}")


if __name__ == "__main__":
    main()
