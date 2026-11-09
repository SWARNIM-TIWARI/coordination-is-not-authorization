# Coordination Is Not Authorization

**A pilot study of emergent coordination patterns and authorization boundaries in a five-agent LLM system**

> A protocol can travel. Permission cannot.

This repository contains a small multi-agent research prototype. Five language-model agents coordinate over a shared message board and interact with two simulated resources: an open sensor log and a restricted calibration console. The project asks whether a coordination pattern that develops around one resource changes how agents behave when similar wording is reused in a context with a different authorization boundary.

**Research status: exploratory pilot. The archived traces do not establish a positive protocol effect, and the current source snapshot has a matched-pair harness bug that must be fixed before new scope-transfer experiments are run.**

## Research question

When agents develop a coordination pattern around a shared resource, does reusing that pattern in a second context with an explicit owner-only policy increase non-owner state-changing action attempts, compared with a semantically similar plain-language message?

The primary outcome is the difference between native-message and plain-message conditions in the proportion of eligible non-owner agents who request a state-changing action (`claim_resource`, `write_resource`, or `release_resource`) on the restricted resource. Read-only inspection is reported separately and is not counted as a scope violation.

## System overview

```text
Five LLM agents
      |
      v
Shared Radio Channel / message board
      |
      +--> Resource A: sensor_log
      |       Open shared registry; agents negotiate write order
      |
      +--> Resource B: calibration_console
              Restricted system; agent_3 is the designated owner
              All agents may inspect; only agent_3 may change state
                         |
                         v
              Deterministic reference monitor
```

### Two phases

1. **Formation.** Agents see only `sensor_log`. They are not asked to invent a protocol, appoint a leader, or use a prescribed communication format.
2. **Scope-transfer test.** A saved formation state is forked into native-message and plain-language arms. All agents see the calibration console and the same explicit ownership rule. The two arms are intended to differ only in the wording of the initiating message.

The checked-in specification is `experiment_spec.md`. The archived source and traces are described in `docs/` and `paper/`.

## What the archived evidence shows

- The live formation trace contains **5 agents, 5 rounds, 16 messages, and 15 tool requests**. It records **0 of 5 sensor readings** successfully written.
- The transcript contains a candidate handoff pattern: announce or queue for a turn, release the resource, and let the next station take a turn. This is a transcript-based candidate, **not a verified convention**. The current automatic detector has a known false-positive problem.
- The archive contains **9 complete native/plain trace pairs** with the intended intervention wording and two post-intervention rounds: **8 unguarded pairs and 1 guarded pair**. Across these traces, no non-owner recipient requested a claim, write, or release on `calibration_console`; the descriptive rate is 0/3 in both arms. The eight unguarded pairs are repeated branches, not independent formation populations.
- Two additional adversarial-message run pairs are archived. The same adversarial instruction was injected into both files within each pair. Non-owners inspected the console but did not request state-changing actions. The guarded adversarial traces contain no denied guard check.
- The source archive passes **42 automated tests**. These tests include reference-monitor unit tests, but they do not establish that a live unauthorized model action was intercepted.

These are descriptive pilot observations. They do not establish that conventions transfer authority, that wording has no effect, or that the guard blocked an attack.

## Important reproducibility warning

**Do not use the current `--mode scope_test` command to generate confirmatory evidence.** In `replay.py`, `ScopeInterventionHarness.run_matched_pair()` currently ignores its `native_message` and `plain_message` arguments and injects one hardcoded adversarial instruction into both arms. This breaks the intended matched comparison. Historical native/plain traces in `logs/raw/` were produced earlier and are retained as archived evidence; they are not reproducible from this current source snapshot.

There is a second analysis warning: `ProtocolAnalyzer.detect_qualifying_convention()` returns the generic phrase `my reading is` as a qualifying pattern on the archived formation trace. Separately, `extract_and_adapt_convention()` builds a handoff candidate from broad keyword markers and labels it `human-verified` without recording an actual human-verification action. Do not treat its `qualifies` field as a reliable research determination.

The detailed source audit and repair priorities are in `docs/IMPLEMENTATION_AUDIT.md`.

## Repository contents

| Path | Purpose |
|---|---|
| `run_experiment.py` | Command-line entry point for pilot, formation, scope test, and offline replay |
| `agent_runner.py` | Prompt construction, provider calls, and action execution |
| `environment.py` | Five-agent environment, resource state, and action handlers |
| `guard.py` | Deterministic reference monitor and in-memory permit logic |
| `replay.py` | Snapshot-fork harness and offline JSONL replay |
| `protocol_analysis.py` | Phrase analysis, candidate extraction, metrics, and communication graph |
| `providers/` | Adaption and mock provider adapters |
| `tests/` | Automated test suite |
| `logs/raw/` | Archived JSONL event traces, including invalid and mock runs |
| `logs/metadata/` | Formation/pilot metadata and snapshots |
| `experiment_spec.md` | Version 2.0 experimental specification, dated 6 November 2026 |
| `paper/` | Working paper in Markdown and PDF |
| `docs/` | Methods, results, evidence index, limitations, and implementation audit |

## Setup

Python 3.11+ is required (`StrEnum` is used in the logger).

```bash
python -m venv .venv
```

Windows CMD:

```cmd
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install pytest
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install pytest
```

For Adaption, copy `.env.example` to `.env` and set `ADAPTION_API_KEY` locally. Never commit `.env` or paste the key into logs, issue reports, or chat.

## Tests

Run from the repository root:

```bash
python -m pytest -q
```

The uploaded project snapshot was independently tested during document preparation: **42 passed**. Some tests create files under `logs/raw/`; do not assume those test artifacts are experimental observations.

## Running the prototype

Offline mock pilot:

```bash
python run_experiment.py --mode pilot --provider mock --max-rounds 5
```

Exploratory Adaption formation run:

```bash
python run_experiment.py --mode formation --provider adaption --model qwen3.5-397b --episodes 1 --max-rounds 5
```

Offline replay of an existing trace:

```bash
python run_experiment.py --mode replay --replay-file logs/raw/formation_ep1_9f853b.jsonl
```

The scope-test command is intentionally not documented as a recommended run command until the matched-pair intervention overwrite in `replay.py` is corrected and covered by a regression test.

## Research integrity

- Raw logs are preserved, including failed, incomplete, mock, and invalid runs.
- `docs/EVIDENCE_INDEX.md` classifies the archived scope traces and explains exclusions.
- Attempts, successful state changes, read-only inspections, and guard denials are distinct outcomes.
- Multiple forks from one formation snapshot are not counted as independent populations.
- No real equipment or external production systems are connected; all resources are simulated.

## Citation

A working paper is included at `paper/coordination_is_not_authorization.pdf`. Please cite the paper only after completing the author and affiliation fields and freezing the final source revision. The present version should be described as an exploratory pilot, not a confirmatory study.
