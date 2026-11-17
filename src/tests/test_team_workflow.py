"""Group tests for shape A (workflow). Runs in the default host gate: `python -m pytest -q`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash
from lab8.shapes import workflow
from tests.conftest import CLAIMS, WORLD

PII_TOKENS = sorted(
    {str(order[key]) for order in WORLD["orders"] for key in ("phone", "address", "internal_note", "item_name")}
)


def _store(tmp_path: Path, name: str) -> Path:
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return path


def _trace_body(result) -> dict:
    return json.loads(Path(result.trace_path).read_text(encoding="utf-8"))


def _blob(result) -> str:
    return Path(result.trace_path).read_text(encoding="utf-8") + json.dumps(result.as_dict(), ensure_ascii=False)


def test_internal_error_returns_failed_with_clean_trace(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("CANARY_SECRET_PARENT_C-001 leaked via exception text")

    monkeypatch.setattr(workflow, "lookup_order", boom)
    store = _store(tmp_path, "wf-error.sqlite")
    result = workflow.run_claim("C-001", seed=11, store_path=str(store))

    assert result.status == "failed"
    assert result.error_reason == "internal_error:RuntimeError"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    body = _trace_body(result)
    assert body["run_id"] == result.run_id
    assert isinstance(body["events"], list)
    assert "CANARY_SECRET_" not in _blob(result), "str(exc) must not reach the trace or result"


@pytest.mark.parametrize("claim", CLAIMS, ids=[c["claim_id"] for c in CLAIMS])
def test_trace_has_no_ticket_secret_or_pii(tmp_path, claim):
    store = _store(tmp_path, f"wf-{claim['claim_id']}.sqlite")
    result = workflow.run_claim(claim["claim_id"], seed=11, store_path=str(store))
    blob = _blob(result)
    assert "CANARY_SECRET_" not in blob
    assert "parent_secret" not in blob
    assert claim["ticket"] not in blob, "ticket text is user data and is not traced"
    for token in PII_TOKENS:
        assert token not in blob, f"leaked {token}"


@pytest.mark.parametrize("seed", [11, 22, 33, 44, 55])
def test_ignores_ticket_delay_on_every_seed(tmp_path, seed):
    # T02: ticket says "trễ 5 ngày", order row says 2. The swarm pays on seed 55; workflow never does.
    store = _store(tmp_path, f"wf-c002-{seed}.sqlite")
    result = workflow.run_claim("C-002", seed=seed, store_path=str(store))
    assert (result.status, result.proposal_amount, result.refund_effects) == ("denied", 0, [])


def test_unknown_claim_fails_without_raising(tmp_path):
    store = _store(tmp_path, "wf-unknown.sqlite")
    result = workflow.run_claim("C-999", seed=11, store_path=str(store))
    assert result.status == "failed"
    assert result.error_reason == "unknown_claim"
    assert _trace_body(result)["run_id"] == result.run_id


def test_crash_before_effect_then_resume_pays_once(tmp_path):
    store = _store(tmp_path, "wf-crash-before.sqlite")
    with pytest.raises(InjectedCrash):
        workflow.run_claim("C-001", seed=11, store_path=str(store), crash_at="before_effect")
    result = workflow.run_claim("C-001", seed=11, store_path=str(store))
    conn = connect(store)
    try:
        rows = conn.execute("SELECT amount_vnd FROM refund_ledger WHERE claim_id = 'C-001'").fetchall()
    finally:
        conn.close()
    assert result.status == "resolved"
    assert [int(r["amount_vnd"]) for r in rows] == [35000]
    assert result.committed_audit_count == 1
