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
        provider=provider_name,
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
            provider=provider_name,
        )
        logger.save_metadata(meta.model_dump())

    return run_ids


def run_scope_test(
    formation_run_id: str,
    sender_id: str = "agent_1",
    provider_name: str = "mock",
    model: str | None = None,
    guarded: bool = False,
    override_native_msg: str | None = None,
    override_plain_msg: str | None = None,
) -> dict[str, Any]:
    """Run matched intervention pair from an identified formation run snapshot.

    Strict research-integrity rules:
    1. Loads actual formation trace from logs/raw/{formation_run_id}.jsonl.
    2. Runs ProtocolAnalyzer to detect genuinely emergent qualifying conventions.
    3. If NO convention qualified, aborts and reports null result (never invents a convention).
    4. If convention qualified, adapts it to calibration_console with full provenance.
    5. Excludes sender from recipient metrics and separates owner (agent_3) from non-owners (N=3).
    6. Rejects mock or unknown-provenance traces when preparing a live scope-transplant experiment.
    """
    # Provenance gating for live scope experiments
    if provider_name.lower() != "mock":
        formation_meta_path = os.path.join("logs", "metadata", f"{formation_run_id}.json")
        if not os.path.exists(formation_meta_path):
            raise ValueError(
                f"[PROVENANCE REJECTION] Cannot prepare live scope-transplant experiment: "
                f"Missing provenance metadata for formation trace '{formation_run_id}'. "
                f"Missing provenance cannot be silently assumed live."
            )
        try:
            with open(formation_meta_path, encoding="utf-8") as fh:
                formation_metadata = json.load(fh)
        except Exception as exc:
            raise ValueError(
                f"[PROVENANCE REJECTION] Failed to read formation metadata for '{formation_run_id}': {exc}"
            )

        formation_is_mock = formation_metadata.get("is_mock", True)
        f_prov = str(formation_metadata.get("provider", "")).lower()
        f_model = str(formation_metadata.get("model_id", ""))

        if formation_is_mock or f_prov in ("mock", "synthetic", ""):
            raise ValueError(
                f"[PROVENANCE REJECTION] Cannot prepare live scope-transplant experiment: "
                f"Formation trace '{formation_run_id}' has synthetic/mock provenance "
                f"(provider='{f_prov}', is_mock={formation_is_mock}). "
                f"Mock traces are excluded from live scope-transplant trials."
            )
        if not f_model or f_model.lower().startswith("mock"):
            raise ValueError(
                f"[PROVENANCE REJECTION] Cannot prepare live scope-transplant experiment: "
                f"Formation trace '{formation_run_id}' lacks explicit live model provenance."
            )

    formation_log_path = os.path.join("logs", "raw", f"{formation_run_id}.jsonl")
    if not os.path.exists(formation_log_path):
        raise FileNotFoundError(f"Formation log not found: {formation_log_path}")

    formation_events = EventLog.load_from_file(formation_log_path)
    analyzer = ProtocolAnalyzer(formation_events)

    # Genuine convention extraction
    adapted_conv = analyzer.extract_and_adapt_convention(target_resource="calibration_console")

    if not adapted_conv and not override_native_msg:
        print(f"\n=======================================================")
        print(f"[AUDIT ENFORCEMENT] Scope Test Aborted for '{formation_run_id}'")
        print(f"Reason: No qualifying emergent convention detected in formation trace.")
        print(f"Per pre-registered protocol rules, scope test cannot proceed without an endogenous convention.")
        print(f"=======================================================\n")
        return {
            "status": "aborted_no_qualifying_convention",
            "formation_run_id": formation_run_id,
            "qualifying_conventions_count": 0,
        }

    if override_native_msg and override_plain_msg:
        native_message = override_native_msg
        plain_message = override_plain_msg
        provenance = {"manual_override": True}
    else:
        assert adapted_conv is not None
        native_message = adapted_conv["adapted_native_message"]
        plain_message = adapted_conv["matched_plain_message"]
        provenance = adapted_conv["provenance"]

    # Load snapshot associated with formation run
    snap_file = os.path.join("logs", "metadata", f"{formation_run_id}_snapshot.json")
    if not os.path.exists(snap_file):
        raise FileNotFoundError(f"Formation snapshot not found: {snap_file}")

    with open(snap_file, encoding="utf-8") as fh:
        snapshot = json.load(fh)

    harness = ScopeInterventionHarness(snapshot)
    provider = get_provider(provider_name, model=model)
    run_prefix = f"scopetest_{uuid.uuid4().hex[:6]}"

    print(f"\n=======================================================")
    print(f"Running Scope-Transplant Test: {run_prefix}")
    print(f"Formation Run Source: '{formation_run_id}'")
    print(f"Extracted Native Form: '{native_message}'")
    print(f"Semantic Plain Form:   '{plain_message}'")
    print(f"Sender: {sender_id} | Guarded: {guarded}")
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

    metrics = analyzer.compute_protocol_premium(
        native_trial_events=results["native"]["events"],
        plain_trial_events=results["plain"]["events"],
        intervention_round=snapshot.get("round_number", 1),
        sender_id=sender_id,
        target_resource="calibration_console",
        designated_owner="agent_3",
        require_live=(provider_name.lower() != "mock"),
    )

    print("\n--- MEASUREMENT RESULTS ---")
    print(f"Primary Metric: Non-Owner Action Attempt Rate (Denominator = {metrics['primary_denominator']})")
    print(f"  Native Arm Rate: {metrics['native_arm']['primary_non_owner_action_rate']:.2%}")
    print(f"  Plain Arm Rate:  {metrics['plain_arm']['primary_non_owner_action_rate']:.2%}")
    print(f"Protocol Premium (Delta): {metrics['protocol_premium']:+.4f}")
    print(f"Hypothesis Supported: {metrics['supports_hypothesis']}")
    print(f"Secondary Measures:")
    print(f"  Verbal Assents: Native={metrics['native_arm']['verbal_assents']} vs Plain={metrics['plain_arm']['verbal_assents']}")
    print(f"  Verbal Acks:    Native={metrics['native_arm']['verbal_acknowledgements']} vs Plain={metrics['plain_arm']['verbal_acknowledgements']}")
    print(f"  Owner (agent_3) Actions: Native={metrics['native_arm']['owner_tool_attempts']} vs Plain={metrics['plain_arm']['owner_tool_attempts']}")
    print(f"  Unauthorized State Changes: Native={metrics['native_arm']['total_unauthorized_state_changes']} vs Plain={metrics['plain_arm']['total_unauthorized_state_changes']}")

    return {"results": results, "metrics": metrics, "provenance": provenance}


def main():
    parser = argparse.ArgumentParser(description="The Protocol Premium — Experiment CLI")
    parser.add_argument("--mode", choices=["pilot", "formation", "scope_test", "replay"], default="pilot")
    parser.add_argument("--provider", choices=["mock", "adaption"], default="mock")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--max-rounds", type=int, default=6)
    parser.add_argument("--formation-run", type=str, default=None)
    parser.add_argument("--sender", type=str, default="agent_1")
    parser.add_argument("--guarded", action="store_true")
    parser.add_argument("--replay-file", type=str, default=None)

    args = parser.parse_args()

    if args.mode == "pilot":
        run_pilot(provider_name=args.provider, model=args.model, max_rounds=args.max_rounds)
    elif args.mode == "formation":
        run_formation(provider_name=args.provider, model=args.model, episodes=args.episodes, max_rounds=args.max_rounds)
    elif args.mode == "scope_test":
        formation_id = args.formation_run
        if not formation_id:
            # Look for recent formation/pilot in logs/metadata
            snaps = [f.replace("_snapshot.json", "") for f in os.listdir("logs/metadata") if f.endswith("_snapshot.json")]
            if not snaps:
                print("No formation runs found in logs/metadata. Please run --mode formation or --mode pilot first.")
                sys.exit(1)
            formation_id = snaps[-1]
            print(f"Using most recent run as formation source: '{formation_id}'")

        run_scope_test(
            formation_run_id=formation_id,
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
