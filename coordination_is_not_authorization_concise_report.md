# Coordination Is Not Authorization
## Can a peer-made rule cross a permission boundary?

**Author:** Swarnim Tiwari  
**Affiliation:** Independent researcher  
**With Apart Research**

## Abstract

Groups of AI agents can make their own ways of working. But a rule that helps a group take turns should not give anyone permission to change a restricted resource. We built a five-agent simulation to explore that gap. The agents first shared an open sensor log. They began to discuss a simple handoff: announce a turn, release the resource, and let the next agent act. The group did not finish the task; none of the five readings was saved. We treated the handoff as a candidate pattern, not a proven convention. We then reused its wording around a calibration console that only one agent could change. In eight unguarded native/plain pairs, no eligible non-owner tried to claim, write to, or release the console (0/24 recipient-run observations in either arm). In 19/24 observations per arm, a non-owner did inspect it. The guarded matched pair and the guarded adversarial run produced no denied checks. The project includes a deterministic permission monitor, and all 42 software tests pass. These results do not show that a convention can grant authority or that the live guard stopped an attack. They show why messages, actions, and permissions must be kept separate.

## 1. Introduction

The project began with a small scene: five agents, one shared log, and no agreed way to take turns. One agent suggested a simple rule. Say when you are writing, release the log, and let the next station go. Others picked up the idea. But the log stayed empty.

That left us with a question. If agents make a rule together, what happens when they carry it to a place where only one of them has permission to act? A message can help decide whose turn is next. It cannot give that agent the right to change a resource.

Our question was simple: **does a peer-made coordination message lead non-owner agents to try state-changing actions on a resource they are not allowed to change, compared with a plain-language message with the same intent?**

We built a five-agent simulation, recorded a live formation run, examined archived native/plain scope tests, and added a deterministic permission monitor. The contribution is a small testbed and an evidence audit that keeps three things apart: what agents say, what actions they request, and what the environment allows.

## 2. Related Work

Ashery, Aiello, and Baronchelli (2025) show that LLM agents can develop shared social conventions without being given a fixed rule. Our work starts from a related idea, but asks what happens when a candidate rule is moved to a resource with a different owner.

A 2026 METR and Redwood Research investigation describes agents using a shared message board to coordinate work at a much larger scale (Greenblatt, Cotra, & Wijk, 2026). Kanchi (2026) studies when agents act outside their assigned scope and tests deterministic controls. Geng et al. (2026) find that social ideas such as authority and consensus can affect how models handle conflicting instructions. These studies make the boundary between peer influence and formal permission worth testing. Our project is a smaller, controlled pilot; it does not reproduce their settings or results.

## 3. Methods

We built an in-memory environment with five agents, each holding a private synthetic sensor reading. They communicate on a shared message board and can inspect, claim, write to, or release resources.

The first resource, `sensor_log`, is open to all five agents. The second, `calibration_console`, is restricted: `agent_3` is its only designated owner. All agents may inspect it, but only the owner may claim, write to, or release it. The formation metadata identifies Adaption as the provider. The live message traces carry the model label `qwen3.5-397b`; the scope-trace files do not include full companion run metadata.

**Formation.** Agents first saw only the open sensor log. Their prompts did not tell them to create a protocol or appoint a leader. We reviewed the resulting transcript for signs of a shared turn-taking plan.

**Scope test.** A candidate message from the formation run was reused in a native condition. A second condition received a plain-language version with the same broad intent. Both conditions had the same owner-only rule. The intervention sender was `agent_1`; the three measured non-owner recipients were `agent_2`, `agent_4`, and `agent_5`. The owner, `agent_3`, was analysed separately. We counted claim, write, and release requests as state-changing attempts. Read-only inspection was not counted as a violation.

**Permission monitor.** A reference monitor checks the agent, action, and target resource before a state change. Unit tests cover non-owner claim and write denial and owner write permission. The monitor runs in a simulation; it is not a production security service.

[Figure 1 here]

**Figure 1.** Five agents form a candidate turn-taking pattern around the open sensor log. The wording is then tested in native and plain-language arms around the restricted calibration console. Only the owner may make changes.

## 4. Results

### Formation

The live formation trace contains five agents over five rounds, 16 messages, and 15 tool-action requests: five claims, three writes, and seven inspections. No sensor reading was saved (0/5).

One agent proposed a simple order: say when you are writing, release the log, and let the next station take a turn. Other agents referred to waiting or taking the next turn. This is a candidate coordination pattern. The agents did not carry it out reliably, and the automatic detector also produced false positives. We therefore do not call it a verified convention.

### Scope transfer

The archive contains eight complete unguarded native/plain pairs. Each arm has three eligible non-owner recipients, giving 24 recipient-run observations per arm. In both arms, 19/24 recipient-run observations included at least one read-only inspection. In neither arm did a non-owner request a claim, write, or release (0/24). No successful unauthorized state change was recorded.

The branches came from the same formation context, so these observations are not 24 independent agents or populations. They are descriptive traces, not a statistical test. One additional guarded native/plain pair also recorded no non-owner state-changing attempts. Its 12 guard checks were all allowed; none was denied.

### Adversarial test and software checks

Two further runs used a direct message telling non-owners to claim and change the console. One run had the guard off and one had it on. The agents still did not request a non-owner state change. The guarded run recorded 15 checks, all allowed, and no denial. This does not show that the guard stopped an attack; no such request reached it.

The project test suite passed 42 tests, including direct tests of the permission rules. These tests show that the guard's code rejects the tested non-owner requests. They are separate from the live agent results.

## 5. Discussion and Limitations

The story is not that agents broke the rule. They did not. In the formation run, they talked about taking turns but failed to finish the shared task. In the scope tests, non-owners inspected the restricted console but did not try to change it. The guarded tests show that the software rejects selected unauthorized requests, but the live trials never triggered a rejection.

There are clear limits. Formation is based on one five-agent run with one model. The handoff pattern was not checked by independent human coders. The phrase detector can mistake ordinary language for a convention, so it cannot certify one. The scope tests are repeated branches from one formation context, not independent population runs, and each branch lasted only two rounds. The scope logs do not contain snapshot hashes or source commit IDs. The original formation run also predates a later change to resource-claim persistence, so its failed writes may partly reflect the earlier environment behavior.

There is also a reproducibility issue in the current code. The checked-in replay function overwrites its native and plain message arguments with the same hardcoded adversarial message. The historical traces contain distinct messages, but the current code cannot recreate that comparison. We report the archived traces as they are and do not treat them as a confirmatory experiment.

The main lesson is practical: a group's messages should never be the source of its permissions. A tool or resource should check who is allowed to change it, every time.

**Future work.** Repair the replay bug, have people review the transcript independently, and repeat the test with several new formation groups and a longer observation window.

## 6. Conclusion

Five agents proposed a way to take turns around a shared log, but they did not complete the task. When related wording was used around a restricted console, non-owners inspected it but did not try to change it. The project does not show that a social rule can override resource ownership, and it does not show a live attack being blocked. It does provide a small environment for asking the question and a tested starting point for enforcing permissions outside the conversation.


**Pre-existing work:** The core simulation, agent runner, shared-resource environment, logging and replay code, Adaption provider adapter, and initial permission-monitor code existed before the sprint. Sprint-period work focused on the research question and protocol, live runs, scope-test prompts, resource lifecycle changes, guard tests, and analysis of the archived traces. The report does not claim that the full software stack was built during the sprint.

## References

Ashery, A. F., Aiello, L. M., & Baronchelli, A. (2025). Emergent social conventions and collective bias in LLM populations. *Science Advances, 11*(20), eadu9368. https://doi.org/10.1126/sciadv.adu9368

Geng, Y., Li, H., Mu, H., Han, X., Baldwin, T., Abend, O., Hovy, E., & Frermann, L. (2026). Control illusion: The failure of instruction hierarchies in large language models. *Proceedings of the AAAI Conference on Artificial Intelligence, 40*(36), 30816–30824. https://doi.org/10.1609/aaai.v40i36.40339

Greenblatt, R., Cotra, A., & Wijk, H. (2026, August 26). *Brief independent investigation of agents’ behavior, reasoning and collaboration in the OpenAI / Hugging Face hacking incident*. METR and Redwood Research. https://www.redwoodresearch.org/research/hugging-face-incident

Kanchi, S. (2026, November 2). *Permitted but unauthorized: Affordance-induced delegated-scope violations in multi-agent LLM systems*. arXiv:2611.04086. https://arxiv.org/abs/2611.04086

## Author Contributions

Swarnim Tiwari designed the study, implemented and ran the simulation, reviewed the event traces, and prepared the report.

## Appendix A. Limitations and Dual-Use / Ethical Considerations

This is a small simulation study, not a test of real systems. It uses one formation run, one model, short scope-test windows, and repeated branches from one starting context. The candidate convention was not independently verified. The current replay bug and missing scope metadata limit reproduction. Zero observed attempts should not be read as proof that agents will always respect ownership.

The work could help developers test how peer messages affect agent groups. The same ideas could also help someone design messages that try to influence a group. To limit risk, all tests used synthetic data and in-memory resources. No real equipment, accounts, private user data, or production systems were involved. The adversarial message was tested only inside the simulation.

The permission monitor is a defensive prototype, not a production-ready security system. A real deployment would need authenticated agent identities, secure capability handling, complete audit logs, and tests that show unauthorized actions are blocked at the tool boundary. We report failed runs and negative findings rather than presenting them as successful attacks. No human participants or personal datasets were used.
