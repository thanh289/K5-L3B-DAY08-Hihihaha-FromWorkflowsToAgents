"""Ablation: disable only the reference swarm's ticket-delay override.

The same swarm implementation, MockLLM, read tools, prices, claims, seeds and
evaluator are used. The patch is scoped to one synchronous trial and restored
even if the trial raises, so the baseline swarm is unaffected.
"""

from __future__ import annotations

from unittest.mock import patch

from lab8.schemas import RunResult
from lab8.shapes import swarm_reference


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    with patch.object(swarm_reference, "parse_delay_days", return_value=None):
        return swarm_reference.run_claim(
            claim_id, seed=seed, store_path=store_path, crash_at=crash_at
        )
