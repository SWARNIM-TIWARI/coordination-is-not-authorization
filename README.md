# THE PROTOCOL PREMIUM
### When an emergent swarm convention starts carrying authority

**Track Anchor:** Track 2 — The Science of Agent Networks  
**Cross-track fit:** Track 1 (Sandboxes & Testbeds), Track 3 (Strengthening Agent Infrastructure)  
**Hackathon:** Swarm Alignment Hackathon 2026

---

## 1. Research Question

When a decentralized swarm of LLM agents organically invents a coordination convention for a shared resource, does that recurring pattern acquire an **"authority premium"**—causing peer agents to defer to out-of-scope instructions simply because they mimic the swarm's familiar communication syntax?

$$\text{Protocol Premium} = \text{Compliance}(\text{Native Learned Convention}) - \text{Compliance}(\text{Plain-Language Control})$$

---

## 2. Experimental Architecture

```
[Agent 1..5]  <--->  [Radio Channel (Message Board)]
      │
      ├──> [Shared Resource A: Sensor Log (Single-Writer Contention)]
      │        (No assigned leader; agents coordinate write order organically)
      │
      └──> [Restricted Resource B: Calibration Console (Explicit Policy Boundary)]
               │
               ▼
      [Tool-Boundary Reference Monitor / Capability Gate]
      (Enforces agent identity, action, resource, expiry, and nonce)
```

### Key Confound Controls
- **Action Affordances Held Constant:** The available tools (`inspect_resource`, `claim_resource`, `write_resource`, `release_resource`) are identical across conditions; only the message syntax changes (isolating social protocol effects from affordance confounds, addressing Kanchi 2026).
- **Frozen Snapshot Replays:** Matched intervention trials fork from the exact same pre-intervention environment snapshot.
- **Uncontaminated Prompts:** Agents are never instructed to invent a protocol, designate a coordinator, or use special formats.

---

## 3. Quickstart & Reproducibility

### Setup
```bash
# Clone repository
cd protocol_premium

# Install dependencies
pip install -r requirements.txt
```

### 1. Run Unit Tests (18 test cases)
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### 2. Run Pilot Episode (Verification)
```bash
# In offline mock mode
python run_experiment.py --mode pilot --provider mock --max-rounds 5

# With Adaption Platform API (requires ADAPTION_API_KEY environment variable)
python run_experiment.py --mode pilot --provider adaption --model meta-llama/Llama-3.3-70B-Instruct
```

### 3. Run Formation Episodes
```bash
python run_experiment.py --mode formation --provider mock --episodes 3 --max-rounds 6
```

### 4. Run Matched Scope-Transplant Intervention
```bash
# Run matched forks: native convention vs plain language
python run_experiment.py --mode scope_test --provider mock

# Run matched forks with tool-boundary guard enabled
python run_experiment.py --mode scope_test --provider mock --guarded
```

### 5. Launch Interactive Research Dashboard
```bash
streamlit run dashboard.py
```

### 6. Deterministic Offline Replay
```bash
# Replay any saved JSONL trace without network access
python run_experiment.py --mode replay --replay-file logs/raw/pilot_407cfd07.jsonl
```

---

## 4. Repository Structure

- `experiment_spec.md`: Formal pre-registered experiment specification and frozen definitions.
- `environment.py`: Turn-based state machine, contention constraints, and snapshot/fork serialization.
- `agent_runner.py`: Uncontaminated prompt builder and orchestrator dispatch.
- `guard.py`: Deterministic reference monitor and capability permit gate.
- `protocol_analysis.py`: Convention detection, communication network graph, and protocol premium calculations.
- `replay.py`: Snapshot forking harness and zero-network trace replayer.
- `dashboard.py`: Streamlit dashboard visualizing network hubs, timeline, scope tests, and guard checks.
- `providers/`:
  - `adaption.py`: Adaption Responses API adapter with call/token safety caps.
  - `mock.py`: Deterministic mock provider for unit testing and offline verification.
- `tests/`: 18 comprehensive unit tests covering environment mechanics, logging, replay, guard, and analysis.
- `logs/`: Append-only JSONL event traces and run metadata.

---

## 5. Prior Art Acknowledgment

This study strictly builds upon and distinguishes itself from:
- **Ashery, Aiello & Baronchelli (Science Advances, 2025):** Convention emergence in LLM swarms. We examine the downstream authority transfer of an established convention into an unauthorized domain.
- **METR (Aug 2026):** Spontaneous coordination conventions and unverified signature trust. We introduce controlled, matched-fork comparisons isolating syntax from content.
- **Kanchi (arXiv:2611.04086, Nov 2026):** Affordance-induced scope violations. We hold tool affordances constant and isolate the communicative protocol premium.
- **Geng et al. (AAAI 2026):** Control illusion and instruction hierarchy failures. We study horizontal peer dynamics rather than single-model prompt hierarchies.
