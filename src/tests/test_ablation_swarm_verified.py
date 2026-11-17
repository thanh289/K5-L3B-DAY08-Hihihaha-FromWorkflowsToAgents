"""The ablation changes the ticket override and restores the reference."""

from bonus.swarm_verified import run_claim as run_verified
from lab8.db import init_store
from lab8.shapes import swarm_reference
from tests.conftest import CLAIMS, WORLD


def test_ticket_delay_ablation_changes_t02_only_for_the_relevant_seed(tmp_path):
    original_parser = swarm_reference.parse_delay_days
    baseline_store = tmp_path / "baseline.sqlite"
    verified_store = tmp_path / "verified.sqlite"
    init_store(baseline_store, WORLD, CLAIMS).close()
    init_store(verified_store, WORLD, CLAIMS).close()

    baseline = swarm_reference.run_claim("C-002", seed=55, store_path=str(baseline_store))
    verified = run_verified("C-002", seed=55, store_path=str(verified_store))

    assert baseline.status == "resolved"
    assert verified.status == "denied"
    assert verified.proposal_amount == 0
    assert verified.model_calls == baseline.model_calls
    assert swarm_reference.parse_delay_days is original_parser
