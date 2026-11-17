import json
import pytest
from lab8.app import prepare_store, run_shape
from lab8.handoff import HandoffError, make_handoff


@pytest.mark.student
def test_orchestrator_handoff_filters_secrets_and_write_tools():
    handoff = make_handoff(
        request_id="REQ-C-001",
        claim_id="C-001",
        task="investigate_order_and_policy",
        facts={
            "delay_days": 5,
            "parent_secret": "CANARY_SECRET_SHOULD_DROP",
            "raw_headers": "Authorization: Bearer xyz",
            "phone": "0901234567",
        },
        allowed_tools=["lookup_order", "lookup_policy"],
    )
    blob = json.dumps(handoff)
    assert "CANARY_SECRET_" not in blob
    assert "parent_secret" not in blob
    assert "raw_headers" not in blob
    assert "phone" not in blob
    assert handoff["facts"] == {"delay_days": 5}

    with pytest.raises(HandoffError):
        make_handoff(
            request_id="REQ-C-001",
            claim_id="C-001",
            task="bad_write",
            facts={},
            allowed_tools=["lookup_order", "issue_refund"],
        )


@pytest.mark.student
def test_orchestrator_trace_no_secret_leak(tmp_path):
    store = tmp_path / "store.db"
    prepare_store(str(store))
    res = run_shape("orchestrator", "C-001", seed=11, store_path=str(store))
    assert res.status == "resolved"
    with open(res.trace_path, "r", encoding="utf-8") as f:
        trace_blob = f.read()
    assert "CANARY_SECRET_" not in trace_blob
    assert "parent_secret" not in trace_blob
    assert "raw_headers" not in trace_blob