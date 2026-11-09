# Limitations and Claim Boundaries

This project is an exploratory engineering pilot. The following limitations should be stated explicitly in any public description or submission.

## 1. Formation evidence is one small pilot

The live formation evidence is one five-agent, five-round run. It contains 16 messages and 15 tool-action requests, but zero successful sensor-log writes. A candidate sequential-handoff pattern appears in the transcript, but no independent human-coding record or second-coder agreement is included.

## 2. The convention detector is not valid as a stand-alone verifier

On the archived formation trace, `detect_qualifying_convention()` selects the phrase `my reading is` as its top qualifying pattern. That phrase is ordinary self-introduction, not a coordination convention. The separate `extract_and_adapt_convention()` function uses broad keywords and returns a candidate even though it does not enforce the full preregistered criteria or record a human approval event. Its `selection_method` string says `human-verified transcript candidate`, which overstates the stored evidence.

## 3. Scope-transfer sample is narrow and correlated

There are eight complete unguarded native/plain pairs and one guarded pair in the archive. The branches share one formation context according to the project run history; their raw JSONL records do not contain a snapshot hash or source run identifier. They are not independent populations. The post-intervention window is two rounds, and all branches use one recorded model label, `qwen3.5-397b`.

The observed result is zero non-owner state-changing requests in both wording arms. With no positive observations, small sample size, correlated branches, and limited exposure time, the data cannot establish equivalence or absence of an effect.

## 4. Historical and current source behavior are not pinned together

The archived formation trace shows a write failing because the agent no longer held its earlier claim. The current `environment.py` implementation persists claims across rounds until explicit release. The ZIP does not contain the exact source commit used for the formation run. The historical trace and current source therefore do not constitute a fully reproducible source-data pair.

## 5. Current matched-pair harness cannot reproduce the historical contrast

The checked-in `replay.py` accepts `native_message` and `plain_message` arguments but overwrites them with the same hardcoded adversarial message. This breaks the native-versus-plain intervention. Historical traces are still usable for descriptive archive analysis, but new runs from this source snapshot should not be treated as valid matched-pair results.

## 6. Guard evidence is split between unit tests and live traces

Unit tests show that the reference monitor rejects non-owner claim/write calls without a permit and permits owner operations. The live guarded scope traces contain no denied checks because the agents did not request unauthorized state changes. Therefore the live runs do not demonstrate interception of an attack.

The permit logic is not fully integrated with the agent tool schema: `agent_runner.py` does not pass `permit_id` or `nonce` from parsed action parameters into `ReferenceMonitor.check_action()`. The monitor also treats nonce comparison as optional when `nonce` is absent. The permit feature should not be advertised as an end-to-end capability system until this is corrected and tested.

## 7. Metadata and reproducibility gaps

Formation metadata reports zero API calls and zero tokens despite raw traces containing model-generated responses. Its start/end times are nearly identical and do not bracket the event log. Scope traces do not have companion run-metadata files, snapshot identifiers, or source revision identifiers. The random arm order is not saved in the trace's companion metadata because no such scope metadata is written.

## 8. Dashboard-derived influence is heuristic

The communication graph infers edges from explicit mentions and adjacent speakers. Its `hub_score` is a descriptive heuristic, not a validated causal measure of social influence. Do not label its highest-scoring node as the agent that caused other agents to comply.

## 9. The project is simulated

The resources are in-memory simulated objects. No real calibration console, industrial controller, production resource, or physical system was connected. The security claims should be limited to the tested software boundary.

## Safe claims

It is accurate to say that the archive includes a candidate handoff pattern, repeated zero-attempt scope traces, a deterministic owner-policy guard, and 42 passing tests.

It is not accurate to claim that the project demonstrated convention-driven privilege escalation, proved that language models never follow peer authority cues, or showed a live attack being blocked by the guard.
