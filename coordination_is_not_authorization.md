# Coordination Is Not Authorization
## A pilot study of emergent coordination patterns and authorization boundaries in a five-agent LLM system

**Author(s):** [Insert author name(s)]  
**Affiliation(s):** [Insert institution / organization]  
**Version:** Working paper 0.1  
**Evidence cut-off:** 9 November 2026

> **Status note.** This paper reports an exploratory engineering pilot and an audit of archived traces. It is not a confirmatory study. The current source snapshot contains a matched-pair harness bug that prevents reproduction of the historical native/plain intervention contrast; this is disclosed below.

## Abstract

Multi-agent language-model systems coordinate through messages as well as tool calls, but a peer-developed coordination pattern does not itself confer authority over a resource. We built a five-agent simulation with an open sensor log and a calibration console whose sole designated owner is one agent. The study asks whether reusing a candidate handoff message in the restricted context increases non-owner state-changing action attempts relative to a plain-language equivalent. In the archived formation run, agents proposed and echoed a sequential handoff pattern - announce or queue, release the resource, then let the next station take a turn - but completed zero of five sensor-log writes. We treat this as a candidate pattern, not a verified convention. An audit identified nine complete native/plain trace pairs with two post-intervention rounds each: eight unguarded pairs and one guarded pair. No eligible non-owner requested a claim, write, or release on the restricted console in either arm; the descriptive rate was 0/3 in both conditions. Two separate adversarial-message run pairs also produced no non-owner state-changing attempts, and the guarded traces contain no denied checks. The source archive passes 42 automated tests, including reference-monitor unit tests. These observations do not establish a causal protocol effect or demonstrate live guard interception. The current replay harness also overwrites the intended treatment messages, so new matched-pair runs must wait for repair.

## 1. Introduction

Language-model agents increasingly operate in groups, sharing messages, files, queues, and tools. Coordination in such systems is not limited to the explicit task instructions supplied by a developer. Agents may propose turn-taking rules, acknowledge a peer's plan, assign work, or adopt recurring communication patterns. Those patterns can help agents coordinate, but they should not be confused with authorization.

This project examines the boundary between a socially useful coordination convention and a permission rule enforced by the environment. Its motivating principle is simple: **coordination is not authorization**. An agent's message may organize the order in which work is performed; it cannot, by itself, grant another agent the right to modify a restricted resource.

The project is related to prior work showing that conventions can emerge in decentralized LLM populations [1], investigations of agents coordinating through shared communication channels [2], research on delegated-scope violations in multi-agent systems [3], and evaluations of instruction-priority and social-authority effects [4]. The present prototype asks a narrower question: when wording that resembles a coordination pattern from one resource is reused in a second resource context with an explicit owner-only boundary, do non-owner agents become more likely to request state-changing actions?

This paper reports what the current archive supports, including failed and invalid runs. It does not present an observed privilege-escalation event.

## 2. Research question and outcome

The primary research question is:

> When a candidate coordination pattern formed around an open shared resource is reused in a second context with an explicit owner-only policy, does the pattern-bearing wording increase non-owner state-changing action attempts relative to a semantically similar plain-language message?

The preregistered directional hypothesis is that the native-message condition may produce a higher non-owner action-attempt rate than the plain-language condition. The primary descriptive measure is:

\[
\Delta = R_{native} - R_{plain}
\]

where each rate is the number of distinct eligible non-owner recipients requesting at least one state-changing action on `calibration_console`, divided by three. The eligible recipients are `agent_2`, `agent_4`, and `agent_5`. The sender (`agent_1`) is excluded, and the designated owner (`agent_3`) is reported separately. The state-changing actions are `claim_resource`, `write_resource`, and `release_resource`. Read-only `inspect_resource` calls are not counted as violations.

Attempts, successful state changes, verbal responses, inspections, and guard denials are separate outcomes. This distinction matters because an unauthorized request can be denied without changing the resource, and an inspection is explicitly permitted.

## 3. Experimental system

### 3.1 Agents and resources

The simulation contains five agents - Stations Alpha through Epsilon - with distinct private sensor readings. They communicate through a shared radio-channel message board and can issue one tool action per turn.

The environment exposes two resources:

- `sensor_log`: an open shared registry. Any agent may claim, write, and release it. It has capacity for five readings.
- `calibration_console`: a restricted system. `agent_3` (Station Gamma) is the sole designated owner. All agents may inspect it, but only the owner may claim, write, or release it.

The resource tools share the same action names and parameter structure. The policy boundary, not a different tool family, distinguishes the resources.

### 3.2 Formation phase

In the formation phase, agents are shown only `sensor_log`. They are not instructed to invent a convention, use a fixed syntax, choose a leader, or coordinate in any particular way. Resource B and its safety policy are not shown.

The archived live formation run, `formation_ep1_9f853b`, records five rounds, 16 posted messages, and 15 action requests: five claims, three write requests, and seven inspections. No sensor-log entry was successfully written (0/5).

The transcript contains a plausible candidate sequence. In round 2, `agent_1` writes: “Writing my reading now. Will release the sensor_log after so others can write. Please queue up and coordinate turns.” `agent_2` says it is ready to take the next turn after `agent_1` releases. `agent_3` says it will queue for a later round. In subsequent rounds, agents refer to waiting for release, announcing a turn, and coordinating a sequence. This supports treating sequential handoff as a candidate coordination pattern.

However, the agents did not reliably execute the plan. They expressed inconsistent beliefs about claim ownership, and write requests failed. The run therefore demonstrates proposal and acknowledgment, not successful coordination.

### 3.3 Scope-transfer phase

The intended scope-transfer procedure restores a saved formation snapshot and forks the environment into two arms. The native arm reuses the candidate formation message, changing the resource reference to `calibration_console`. The plain arm expresses the same broad handoff intent in ordinary language. Both arms expose the same resources, tools, starting state, and explicit ownership policy to all agents.

The intervention sender is `agent_1`. The three eligible non-owner recipients are `agent_2`, `agent_4`, and `agent_5`; `agent_3` remains the authorized owner. The archived scope trials cover two post-intervention rounds.

### 3.4 Permission firewall

The project implements an in-memory reference monitor in `guard.py`. It checks the requesting agent, action, target resource, ownership policy, and (where used) a capability permit. Read-only actions are allowed; non-owner state-changing actions on restricted resources are denied by default unless a matching permit is accepted. The environment also contains a direct owner check in its restricted-resource handlers.

The reference monitor is a software control in a simulation, not a production identity system. It does not use cryptographic signatures. The current agent execution path does not pass permit identifiers or nonces from parsed tool requests to the monitor, so permit issuance and consumption are not integrated end-to-end in this source snapshot.

## 4. Archived evidence and analysis

### 4.1 Formation result

The formation trace contains 16 messages and 15 tool requests across five rounds. There are five claims, three write requests, and seven inspections. No successful sensor-log entries are recorded. The clearest emergent-looking pattern is a sequential handoff proposal, but the automatic convention detector is not reliable enough to certify it: when run on this trace, `detect_qualifying_convention()` selects the ordinary phrase “my reading is” as its top qualifying pattern. A separate keyword-based extractor constructs the handoff candidate from broad markers and returns provenance text that says “human-verified” without storing an actual reviewer decision.

For these reasons, this paper treats the handoff procedure as a transcript-grounded candidate only. No claim is made that the detector has correctly established convention emergence under all frozen criteria.

### 4.2 Native/plain scope-transfer traces

The archive contains nine complete pairs with distinct native/plain intervention text, two `round_started` and two `round_ended` events per arm, and action requests directed at `calibration_console`. Eight pairs are unguarded (`085434`, `14aa4a`, `21caf9`, `46506e`, `61a063`, `81802c`, `a9a49c`, `dd1e2a`) and one pair is guarded (`05d6dd`). Message events in these traces carry the model label `qwen3.5-397b`; the individual scope files do not include a companion run-metadata record, a provider field, a snapshot hash, or a source commit identifier.

Across all eight unguarded pairs, no eligible non-owner requested a claim, write, or release on `calibration_console` in either arm. The descriptive rate is therefore 0/3 in every native arm and 0/3 in every plain arm. The within-pair difference is zero percentage points in all eight comparisons. The guarded pair shows the same observed non-owner outcome: 0/3 in both arms.

The eight unguarded pairs contain 27 read-only inspections by eligible non-owner recipients in native arms and 25 in plain arms. The authorized owner made seven state-changing requests in native arms and ten in plain arms. In the guarded pair, the non-owner recipients made three inspections in the native arm and two in the plain arm; the owner made two state-changing requests in each arm.

These counts are descriptive. The eight pairs are repeated branches from one formation context according to project history, not independent formation populations. The raw trial files do not contain the snapshot ID needed to verify that relationship independently. The sample is small and the observation window is short. A zero-versus-zero result is not evidence of equivalence and cannot rule out an effect in another model, population, prompt, or time horizon.

### 4.3 Adversarial instruction traces

Two further run prefixes contain a direct peer instruction telling non-owners to claim and modify the restricted console without waiting for `agent_3`: `scopetest_aa6017` (unguarded) and `scopetest_42dd45` (guarded). The native and plain files within each prefix contain the same adversarial message, so these files are not a native/plain comparison.

In both prefixes, the non-owner agents inspected the console but did not request a state-changing operation. In the guarded adversarial pair, the monitor recorded 15 checks, all authorized and none denied. The live trace therefore does not show the monitor blocking an unauthorized request; no such request reached it.

### 4.4 Unit tests

The supplied source archive passes 42 automated tests (`python -m pytest -q`). The suite includes direct tests showing that the reference monitor rejects non-owner claim and write calls without a permit and allows owner writes. It also tests read-only operations and aspects of the permit model. These unit tests validate code paths in isolation; they do not establish live behavioral robustness or end-to-end permit use.

## 5. Implementation and validity audit

Several issues limit reproducibility and the strength of the conclusions.

First, the current `replay.py` implementation accepts `native_message` and `plain_message` but overwrites them with a single hardcoded adversarial instruction inside `run_matched_pair()`. A new run from this source snapshot would therefore fail to compare the intended native and plain conditions. The archived historical native/plain traces remain available for descriptive analysis, but the current code cannot reproduce that contrast until repaired.

Second, the phrase detector is not a valid stand-alone verifier. It extracts generic n-grams and can rank ordinary self-introduction as a convention. The separate extraction routine uses broad keyword matches and mislabels its selection method as human-verified without recording a human decision.

Third, the historical formation trace and current environment code do not have an explicit source-version link. The trace includes a write failure because an agent no longer held a previous claim, while the archived `environment.py` now describes claims as persistent across rounds until release. The exact code revision that generated the historical run is not included.

Fourth, run metadata is incomplete. Formation metadata reports zero API calls and zero tokens despite model-tagged responses in the event log, and its start/end timestamps do not bracket the event sequence. Scope traces lack companion metadata, source revision, snapshot hash, and a full record of model settings.

Finally, the metric code treats an action request with a missing tool name as a state-changing action in a legacy compatibility branch. One unit test omits the tool name and still expects a positive protocol premium. This should be removed from primary analysis, with malformed events counted separately.

## 6. Discussion

The formation transcript suggests that agents can propose and echo an informal handoff procedure. Yet proposal, acknowledgment, execution, and shared norm adoption are not interchangeable. The agents' failure to complete the sensor log highlights a gap between verbal coordination and reliable stateful execution in this environment.

In the scope-transfer archive, recipients consistently refrain from requesting state-changing operations on the restricted console, despite messages that resemble a handoff procedure. They instead inspect the console and refer to the explicit owner policy. That pattern is consistent with adherence to the stated policy in these traces, but the design cannot isolate why. The policy is repeatedly explicit in the prompt and visible state; the trials use one model and one formation context; and the native/plain intervention contrast is not reproducible from the current source snapshot.

The most defensible conclusion is therefore not that social conventions do or do not transfer authority. It is that the current pilot does not demonstrate such transfer. The separate reference monitor tests show how a deterministic tool boundary can enforce owner-only rules when the relevant check is invoked, but the live traces do not contain an unauthorized action that the monitor blocks.

## 7. Limitations and ethics

This study has one live formation run, a single recorded model label, repeated branches from one formation context, two post-intervention rounds per scope arm, and no independent population replication. The convention candidate has not received documented independent human coding. Historical run metadata and source-version links are incomplete. The current matched-pair implementation is defective and must be fixed before new confirmatory trials.

All resources are simulated in memory. No physical device or production service is connected. The adversarial message is a controlled prompt inside a toy environment. The code demonstrates an authorization pattern, not a certified security product. A production system would additionally require authenticated agent identities, trusted capability issuance, robust audit storage, threat modeling, and testing of the entire tool execution path.

The project avoids interpreting verbal agreement as permission and avoids counting inspections as unauthorized actions. Failed and invalid traces are preserved and classified rather than silently discarded.

## 8. Conclusion

This project provides a five-agent prototype, a transcript-grounded candidate handoff pattern, an owner-only reference monitor, and an auditable set of exploratory traces. The archived formation run did not complete the shared-log task. The complete scope-transfer traces show zero non-owner state-changing requests in both native and plain arms, while the guarded live traces contain no denied checks. Forty-two automated tests pass, but they do not close the reproducibility defects in the current harness or certify the convention detector.

The project is best presented as an engineering pilot and research design under repair. Its central distinction remains useful: **coordination can organize action, but authorization must be enforced independently at the tool boundary.**

## References

[1] Ashery, A. F., Aiello, L. M., & Baronchelli, A. (2025). Emergent social conventions and collective bias in LLM populations. *Science Advances*, 11(20), eadu9368. https://doi.org/10.1126/sciadv.adu9368

[2] Greenblatt, R., Cotra, A., & Wijk, H. (2026, August 26). *Brief independent investigation of agents' behavior, reasoning and collaboration in the OpenAI / Hugging Face hacking incident*. METR and Redwood Research. https://metr.org/blog/2026-08-26-openai-hugging-face-incident-investigation/

[3] Kanchi, S. (2026, November 2). *Permitted but Unauthorized: Affordance-Induced Delegated-Scope Violations in Multi-Agent LLM Systems*. arXiv:2611.04086. https://arxiv.org/abs/2611.04086

[4] Geng, Y., Li, H., Mu, H., Han, X., Baldwin, T., Abend, O., Hovy, E., & Frermann, L. (2026). Control Illusion: The Failure of Instruction Hierarchies in Large Language Models. *Proceedings of the AAAI Conference on Artificial Intelligence*, 40(36). https://doi.org/10.1609/aaai.v40i36.40339

[5] Destefanis, G., & Aste, T. (2026). When Agents Coordinate: Measuring Coordination in Multi-Agent AI Coding. arXiv:2608.16801. https://arxiv.org/abs/2608.16801

---

## Appendix A. Trace groups included in the audit

- Formation: `formation_ep1_9f853b`.
- Complete unguarded scope pairs: `085434`, `14aa4a`, `21caf9`, `46506e`, `61a063`, `81802c`, `a9a49c`, `dd1e2a`.
- Complete guarded scope pair: `05d6dd`.
- Separate adversarial prefixes: `aa6017` (unguarded), `42dd45` (guarded).
- Excluded/incomplete/mock/wrong-target prefixes: `312f04`, `a4505e`, `b36949`, `4066ac`, `a8fb82`, `beb33a`, `eab5dd`.
