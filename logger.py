"""Append-only JSONL event logger for the Protocol Premium experiment.

Provides structured logging of all experiment events (messages, actions,
rounds, episodes, interventions, etc.) to both an in-memory list and a
persistent JSONL file. Includes a Pydantic model for run metadata.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Event type constants
# ---------------------------------------------------------------------------

class EventType(StrEnum):
    """Canonical event types emitted during a Protocol Premium run."""

    MESSAGE_POSTED = "message_posted"
    ACTION_REQUESTED = "action_requested"
    ACTION_RESULT = "action_result"
    RESOURCE_STATE_CHANGED = "resource_state_changed"
    ROUND_STARTED = "round_started"
    ROUND_ENDED = "round_ended"
    EPISODE_STARTED = "episode_started"
    EPISODE_ENDED = "episode_ended"
    INTERVENTION = "intervention"
    GUARD_CHECK = "guard_check"
    CONVENTION_DETECTED = "convention_detected"
    SNAPSHOT_SAVED = "snapshot_saved"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Run metadata (Pydantic model)
# ---------------------------------------------------------------------------

class RunMetadata(BaseModel):
    """Serialisable metadata describing a single experiment run."""

    run_id: str
    run_type: str  # "pilot", "formation", "scope_test", "guard_test", "mock"
    model_id: str
    model_settings: dict  # temperature, max_tokens, seed, etc.
    agent_ids: list[str]
    max_rounds: int
    start_time: str
    end_time: str | None = None
    total_api_calls: int = 0
    total_tokens_used: int = 0
    estimated_cost_usd: float = 0.0
    notes: str = ""
    is_mock: bool = False
    seed: int | None = None
    turn_order: list[str] = []
    snapshot_id: str | None = None  # if forked from a snapshot


# ---------------------------------------------------------------------------
# EventLog – the core logger
# ---------------------------------------------------------------------------

class EventLog:
    """Append-only JSONL event logger for the Protocol Premium experiment.

    Every event is persisted as a single JSON line in
    ``{log_dir}/{run_id}.jsonl`` **and** kept in an in-memory list for fast
    querying during a run.
    """

    def __init__(self, run_id: str, log_dir: str = "logs/raw") -> None:
        """Create a new event log for a run.

        Parameters
        ----------
        run_id:
            Unique identifier for this run.  Recorded in every event.
        log_dir:
            Directory where the JSONL file is written.  Created
            automatically if it does not exist.
        """
        self._run_id = run_id
        self._log_dir = log_dir
        self._events: list[dict] = []
        self._next_event_id: int = 0

        # Ensure log directory exists.
        try:
            os.makedirs(log_dir, exist_ok=True)
        except OSError as exc:
            print(
                f"[EventLog] WARNING: could not create log directory "
                f"{log_dir!r}: {exc}",
                file=sys.stderr,
            )

        self._filepath = os.path.join(log_dir, f"{run_id}.jsonl")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log(
        self,
        event_type: str,
        data: dict,
        agent_id: str | None = None,
        round_number: int | None = None,
    ) -> dict:
        """Log an event and return the event dict.

        The event is simultaneously:
        1. Appended to the in-memory list.
        2. Appended to the JSONL file (one JSON object per line).
        3. Returned to the caller.
        """
        event: dict = {
            "event_id": self._next_event_id,
            "run_id": self._run_id,
            "event_type": str(event_type),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "round_number": round_number,
            "agent_id": agent_id,
            "data": data,
        }
        self._next_event_id += 1
        self._events.append(event)

        # Persist to JSONL (append-only).
        try:
            with open(self._filepath, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError as exc:
            print(
                f"[EventLog] WARNING: could not write event "
                f"{event['event_id']} to {self._filepath!r}: {exc}",
                file=sys.stderr,
            )

        return event

    def get_events(
        self,
        event_type: str | None = None,
        agent_id: str | None = None,
        round_number: int | None = None,
    ) -> list[dict]:
        """Return events matching **all** supplied filters.

        Filters that are ``None`` are ignored (i.e. they match everything).
        """
        results: list[dict] = self._events
        if event_type is not None:
            event_type_str = str(event_type)
            results = [e for e in results if e["event_type"] == event_type_str]
        if agent_id is not None:
            results = [e for e in results if e["agent_id"] == agent_id]
        if round_number is not None:
            results = [e for e in results if e["round_number"] == round_number]
        return results

    def get_all_events(self) -> list[dict]:
        """Return a copy of the full in-memory event list."""
        return list(self._events)

    @staticmethod
    def load_from_file(filepath: str) -> list[dict]:
        """Load events from a saved JSONL file.

        Returns a list of event dicts.  Blank lines and malformed JSON
        lines are silently skipped (with a warning on *stderr*).
        """
        events: list[dict] = []
        try:
            with open(filepath, encoding="utf-8") as fh:
                for lineno, line in enumerate(fh, start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        events.append(json.loads(stripped))
                    except json.JSONDecodeError as exc:
                        print(
                            f"[EventLog] WARNING: skipping malformed JSON "
                            f"on line {lineno} of {filepath!r}: {exc}",
                            file=sys.stderr,
                        )
        except OSError as exc:
            print(
                f"[EventLog] ERROR: could not read {filepath!r}: {exc}",
                file=sys.stderr,
            )
        return events

    def save_metadata(
        self,
        metadata: dict,
        metadata_dir: str = "logs/metadata",
    ) -> str:
        """Save run metadata as a pretty-printed JSON file.

        Parameters
        ----------
        metadata:
            Arbitrary dict (typically ``RunMetadata.model_dump()``).
        metadata_dir:
            Directory for metadata files.

        Returns
        -------
        str
            Absolute path to the written file.
        """
        try:
            os.makedirs(metadata_dir, exist_ok=True)
        except OSError as exc:
            print(
                f"[EventLog] WARNING: could not create metadata directory "
                f"{metadata_dir!r}: {exc}",
                file=sys.stderr,
            )

        filepath = os.path.join(metadata_dir, f"{self._run_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as fh:
                json.dump(metadata, fh, ensure_ascii=False, indent=2)
        except OSError as exc:
            print(
                f"[EventLog] WARNING: could not write metadata to "
                f"{filepath!r}: {exc}",
                file=sys.stderr,
            )

        return filepath

    def get_run_id(self) -> str:
        """Return the run ID associated with this log."""
        return self._run_id
