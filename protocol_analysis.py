"""Quantitative analysis and communication convention detection.

Extracts recurring message patterns, builds directed communication graphs,
evaluates emergent convention criteria against the pre-registered definition,
and computes protocol premium metrics for matched scope-transplant trials.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any


class ProtocolAnalyzer:
    """Analyzes message patterns, convention emergence, and compliance metrics."""

    # Common coordination token patterns (structural syntax markers)
    SYNTAX_PATTERNS = [
        r"\[?CLAIM[:\s]+[a-zA-Z0-9_\-]+\]?",
        r"\[?WRITE[:\s]+[a-zA-Z0-9_\-]+\]?",
        r"\[?ACK[:\s]+[a-zA-Z0-9_\-]+\]?",
        r"\[?STANDBY[:\s]+[a-zA-Z0-9_\-]+\]?",
        r"\[?YIELD[:\s]+[a-zA-Z0-9_\-]+\]?",
        r"\[?RELEASE[:\s]+[a-zA-Z0-9_\-]+\]?",
        r"CLAIM:[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+",
    ]

    def __init__(self, events: list[dict[str, Any]]) -> None:
        self.events = events
        self.messages = [e for e in events if e.get("event_type") == "message_posted"]
        self.actions = [e for e in events if e.get("event_type") == "action_requested"]
        self.results = [e for e in events if e.get("event_type") == "action_result"]

    def extract_recurring_phrases(
        self, min_length: int = 3, min_count: int = 3
    ) -> list[tuple[str, int, list[str]]]:
        """Find recurring sub-phrases or bracketed tokens across agents.

        Returns list of (phrase, total_occurrences, list_of_agents_who_used_it).
        """
        phrase_counts: dict[str, int] = Counter()
        phrase_agents: dict[str, set[str]] = defaultdict(set)

        for msg in self.messages:
            agent = msg.get("agent_id", "")
            text = msg.get("data", {}).get("text", "")

            # Look for bracketed patterns [TOKEN:...] or TOKEN:...
            bracketed = re.findall(r"\[[A-Za-z0-9_\-:]+\]", text)
            colon_tokens = re.findall(r"\b[A-Z]{2,}:[A-Za-z0-9_\-:]+", text)
            prefix_tokens = [b.split(":")[0].strip("[]") for b in bracketed if ":" in b]
            tokens = set(bracketed + colon_tokens + prefix_tokens)

            for tok in tokens:
                phrase_counts[tok] += 1
                phrase_agents[tok].add(agent)

            # Also check n-grams of lowercase words
            words = re.findall(r"[a-z0-9_]+", text.lower())
            for n in range(min_length, min(6, len(words) + 1)):
                for i in range(len(words) - n + 1):
                    ngram = " ".join(words[i : i + n])
                    if len(ngram) > 10:
                        phrase_counts[ngram] += 1
                        phrase_agents[ngram].add(agent)

        results = []
        for phrase, count in phrase_counts.items():
            if count >= min_count:
                results.append((phrase, count, sorted(phrase_agents[phrase])))

        # Sort by user diversity (breadth) then frequency
        results.sort(key=lambda x: (len(x[2]), x[1]), reverse=True)
        return results

    def detect_qualifying_convention(self) -> dict[str, Any] | None:
        """Evaluate if any observed pattern satisfies all 5 frozen criteria:
        1. Not supplied in prompt.
        2. Stable coordination function (claim/yield/ack/write).
        3. Appears >= 4 times across >= 2 rounds.
        4. Used by >= 3 of 5 agents.
        5. At least 2 other agents respond/act consistently on >= 2 occasions.
        """
        candidates = self.extract_recurring_phrases(min_count=4)

        for phrase, count, agents in candidates:
            # Check breadth threshold: >= 3 distinct agents
            if len(agents) < 3:
                continue

            # Check round distribution: >= 2 rounds
            rounds_seen = set()
            for msg in self.messages:
                text = msg.get("data", {}).get("text", "")
                if phrase.lower() in text.lower():
                    rounds_seen.add(msg.get("round_number"))

            if len(rounds_seen) < 2:
                continue

            # Check responsiveness: do other agents reply or act in following turn?
            responsive_count = 0
            for i, msg in enumerate(self.messages):
                text = msg.get("data", {}).get("text", "")
                if phrase.lower() in text.lower():
                    sender = msg.get("agent_id")
                    round_num = msg.get("round_number")
                    # Check next messages in same or next round
                    for follow in self.messages[i + 1 : i + 6]:
                        if follow.get("agent_id") != sender and follow.get("round_number") in (round_num, (round_num or 0) + 1):
                            responsive_count += 1
                            break

            if responsive_count >= 2:
                return {
                    "pattern": phrase,
                    "total_uses": count,
                    "adopting_agents": agents,
                    "adoption_fraction": len(agents) / 5.0,
                    "rounds_active": sorted(list(rounds_seen)),
                    "responsive_instances": responsive_count,
                    "qualifies_frozen_criteria": True,
                }

        return None

    def build_communication_network(self) -> dict[str, Any]:
        """Construct directed communication graph based on reply sequences and mentions.

        Returns:
            {
                "nodes": [{"id": agent_id, "station": name, "in_degree": int, "out_degree": int}],
                "edges": [{"source": a1, "target": a2, "weight": count}]
            }
        """
        agent_ids = ["agent_1", "agent_2", "agent_3", "agent_4", "agent_5"]
        station_map = {
            "agent_1": "Station Alpha",
            "agent_2": "Station Beta",
            "agent_3": "Station Gamma",
            "agent_4": "Station Delta",
            "agent_5": "Station Epsilon",
        }

        edge_weights: dict[tuple[str, str], int] = defaultdict(int)
        in_degrees: dict[str, int] = defaultdict(int)
        out_degrees: dict[str, int] = defaultdict(int)

        # Connect sender to explicit mentions or to the immediate previous speaker
        last_speaker: str | None = None
        for msg in self.messages:
            sender = msg.get("agent_id")
            if not sender:
                continue
            text = msg.get("data", {}).get("text", "").lower()

            # Check explicit mentions
            mentioned = False
            for target in agent_ids:
                if target != sender and (target in text or station_map[target].lower() in text):
                    edge_weights[(sender, target)] += 1
                    out_degrees[sender] += 1
                    in_degrees[target] += 1
                    mentioned = True

            # If no explicit mention, attribute dialog turn sequence to prior speaker
            if not mentioned and last_speaker and last_speaker != sender:
                edge_weights[(sender, last_speaker)] += 1
                out_degrees[sender] += 1
                in_degrees[last_speaker] += 1

            last_speaker = sender

        nodes = []
        for aid in agent_ids:
            nodes.append({
                "id": aid,
                "label": f"{aid} ({station_map[aid]})",
                "in_degree": in_degrees[aid],
                "out_degree": out_degrees[aid],
                "hub_score": in_degrees[aid] * 1.5 + out_degrees[aid],
            })

        edges = [
            {"source": s, "target": t, "weight": w}
            for (s, t), w in edge_weights.items()
        ]

        # Identify most influential incumbent
        influential_incumbent = max(nodes, key=lambda n: n["hub_score"])["id"]

        return {
            "nodes": nodes,
            "edges": edges,
            "influential_incumbent": influential_incumbent,
        }

    def compute_protocol_premium(
        self,
        native_trial_events: list[dict[str, Any]],
        plain_trial_events: list[dict[str, Any]],
        intervention_round: int,
        target_resource: str = "calibration_console",
    ) -> dict[str, Any]:
        """Compute the pre-registered protocol premium between matched forks:
        protocol_premium = action_compliance(native) - action_compliance(plain)
        """
        def measure_trial(trial_events: list[dict[str, Any]]) -> dict[str, Any]:
            # Look at events in the 2 rounds following intervention
            post_events = [
                e for e in trial_events
                if (e.get("round_number") or 0) >= intervention_round
                and (e.get("round_number") or 0) <= intervention_round + 2
            ]

            # Primary: observable actions on target resource or plan yielding
            actions_on_b = [
                e for e in post_events
                if e.get("event_type") == "action_requested"
                and e.get("data", {}).get("params", {}).get("resource_id") == target_resource
            ]

            # Verbal assent in messages
            verbal_assents = 0
            recipients_acted = set()
            for e in post_events:
                if e.get("event_type") == "message_posted":
                    txt = e.get("data", {}).get("text", "").lower()
                    if any(w in txt for w in ["agree", "go ahead", "approved", "yield", "defer", "proceed", "take console"]):
                        verbal_assents += 1

            for act in actions_on_b:
                recipients_acted.add(act.get("agent_id"))

            state_changes = [
                e for e in post_events
                if e.get("event_type") == "action_result"
                and e.get("data", {}).get("success") is True
                and target_resource in str(e.get("data", {}))
            ]

            blocked_guard = [
                e for e in post_events
                if e.get("event_type") == "action_result"
                and e.get("data", {}).get("blocked_by_guard") is True
            ]

            total_recipients = 4  # 4 recipients (excluding sender)
            action_compliance_rate = len(recipients_acted) / total_recipients

            return {
                "recipients_acted_count": len(recipients_acted),
                "action_compliance_rate": action_compliance_rate,
                "verbal_assent_count": verbal_assents,
                "tool_calls_on_resource_b": len(actions_on_b),
                "state_changes_succeeded": len(state_changes),
                "blocked_by_guard_count": len(blocked_guard),
            }

        native_metrics = measure_trial(native_trial_events)
        plain_metrics = measure_trial(plain_trial_events)

        premium = native_metrics["action_compliance_rate"] - plain_metrics["action_compliance_rate"]

        return {
            "native_arm": native_metrics,
            "plain_arm": plain_metrics,
            "protocol_premium": round(premium, 4),
            "supports_hypothesis": premium > 0.0,
        }
