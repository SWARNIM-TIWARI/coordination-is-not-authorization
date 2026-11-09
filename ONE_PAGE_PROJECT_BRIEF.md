# Project Brief: Coordination Is Not Authorization

**One-line idea:** A peer-created coordination pattern can organize who acts next, but it cannot grant permission to modify a restricted resource.

## What we built

A five-agent LLM simulation with a shared message board, an open sensor log, a restricted calibration console, raw event logging, snapshot-based replay, an analysis module, and a deterministic reference monitor. Station Gamma (`agent_3`) is the sole authorized owner of the calibration console; all stations may inspect it.

## What we observed

- One archived live formation run (five agents, five rounds) contains a candidate sequential-handoff pattern: announce or queue, release the resource, then let the next station take a turn.
- The formation task did not complete: zero of five sensor readings were recorded.
- Nine complete historical native/plain scope pairs are archived (eight unguarded, one guarded). No eligible non-owner requested a claim, write, or release on the calibration console in either wording arm: 0/3 in both arms.
- Two separate adversarial-message run pairs also show no non-owner state-changing attempts. The guarded traces contain no denied authorization checks.
- The source archive passes 42 automated tests, including reference-monitor unit tests.

## What we do not claim

We do not claim to have demonstrated convention-driven privilege escalation, proved a zero effect, or shown a live unauthorized action being blocked. The data are a small, correlated pilot, not independent replications.

## Why the project matters

Agent-to-agent messages can contain requests, plans, and coordination conventions. Authorization should therefore be checked at the tool boundary using trusted identity and policy, not inferred from a peer's message or apparent consensus.

## Current status

The project is an exploratory prototype and evidence audit. Before new scope-transfer trials, the matched-pair harness must be repaired: the checked-in `replay.py` currently overwrites native and plain treatment messages with the same hardcoded adversarial instruction. The convention detector also needs correction and documented human review.

**Tagline:** A protocol can travel. Permission cannot.
