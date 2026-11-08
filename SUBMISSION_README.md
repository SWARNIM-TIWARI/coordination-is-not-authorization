THE PROTOCOL PREMIUM

When a swarm's own communication conventions become a source of authority

A protocol can travel. Permission cannot.

Research question

When agents spontaneously develop communication conventions through interaction, do those conventions acquire social influence beyond their original context?

Main finding

A live five-agent formation pilot using Adaption's Qwen3.5-397B model produced a recurring coordination proposal: announce or queue for a turn, release the shared resource, and let the next station take its turn.

However, the agents did not reliably execute this procedure. The five-round run ended with zero of five readings recorded. Agents also displayed inconsistent beliefs about resource ownership and claim status.

Scope-transfer experiment

The first live matched-pair transfer attempt was invalid. Agents continued interacting with the original unrestricted "sensor_log" rather than the restricted "calibration_console".

Consequently, the reported zero-versus-zero comparison is not a valid null result. No Protocol Premium estimate is reported.

Engineering contribution

The project implements a multi-agent resource environment, event logging, snapshot-based experiments, analysis tools, and a deterministic permission-firewall component.

The project test suite previously passed 39 tests.

Conclusion

The pilot demonstrates that agents can negotiate and acknowledge a coordination procedure without reliably executing it.

It does not establish that an emergent convention transfers authority or causes unauthorized actions.

The central engineering principle is:

Coordination is not authorisation.

Limitations

- One live formation episode.
- One model/provider configuration.
- No independent replication.
- No valid scope-transfer result.
- Candidate convention requires independent transcript coding.
- Run metadata contains inconsistencies that should be corrected.

Ethical considerations

All experiments use simulated resources. No real-world safety-critical equipment is connected. Authorization must be enforced by deterministic access controls rather than conversational agreement.