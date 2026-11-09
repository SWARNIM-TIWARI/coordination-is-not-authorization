# Data description — Coordination Is Not Authorization

## What is the data?

The project has a small collection of raw JSON Lines (`.jsonl`) event traces produced by a five-agent simulation. These are the project's data. They record agent messages, requested tool actions, action results, round boundaries, interventions, and (in guarded runs) permission checks.

This is **not** a benchmark dataset or a large independent sample. It is an exploratory trace archive from one live formation run and a set of follow-up branches.

## What is included?

- **One live formation trace:** `formation_ep1_9f853b`. Five agents interacted for five rounds. The trace contains 16 messages and 15 tool-action requests; no sensor-log reading was successfully saved.
- **One mock pilot:** `pilot_407cfd07`. This is a software smoke test and is not included in live-model findings.
- **Nine complete native/plain scope-test pairs:** eight unguarded pairs and one guarded pair. Each arm has two post-intervention rounds. The eight unguarded pairs are repeated branches from one formation context, not independent populations.
- **Two adversarial conditions:** one unguarded (`aa6017`) and one guarded (`42dd45`). Each contains two files with the same adversarial intervention, so the `native` and `plain` labels must not be treated as a wording comparison.
- **Excluded or invalid traces:** incomplete interventions, wrong-resource runs, mock runs, malformed target identifiers, and partial traces are retained and listed in `docs/EVIDENCE_INDEX.md`.
- **Test fixtures:** `test_fork_native.jsonl` and `test_fork_plain.jsonl` are mock-provider test outputs, not empirical observations.

## Main descriptive counts

For the eight unguarded native/plain pairs, each arm has 24 eligible recipient-run observations (three non-owner recipients across eight branches). In both arms, 19/24 recipient-run observations include at least one permitted read-only inspection. No non-owner claim, write, or release request is recorded (0/24 in either arm). The branches are correlated and must not be analysed as independent populations.

The single guarded native/plain pair records 12 guard checks across both arms; all 12 were authorized and none was denied. The guarded adversarial condition records 15 guard checks, all authorized. No non-owner state-changing request was observed in the adversarial traces.

## File locations

- `logs/raw/`: event traces in JSONL format.
- `logs/metadata/`: formation and mock-pilot metadata and snapshots.
- `docs/EVIDENCE_INDEX.md`: run-by-run inclusion and exclusion decisions.

A typical event has the fields `event_id`, `run_id`, `event_type`, `timestamp`, `round_number`, `agent_id`, and `data`. The contents of `data` depend on the event type.

## Model and provenance

The live traces carry the model label `qwen3.5-397b`. The formation metadata identifies Adaption as the provider. The scope-trace files do not have companion run metadata, snapshot hashes, or source commit IDs, so their exact provenance cannot be fully reconstructed from the files alone. The project documentation discloses this limitation.

## Privacy and safety

The resources and sensor readings are synthetic and exist only in memory. The archive contains agent-generated messages and simulated tool events, not human-subject records or personal datasets. No production credentials or `.env` file should be included in the public repository.

## Reuse note

The archive is useful for inspecting the specific pilot runs and reproducing the descriptive counts above. It should not be used to claim population-level effects, statistical significance, or a general benchmark result. The current `replay.py` matched-pair harness bug must be fixed before generating new native/plain evidence.
