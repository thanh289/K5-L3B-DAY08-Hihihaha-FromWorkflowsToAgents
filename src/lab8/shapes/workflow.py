"""Shape A — deterministic workflow. Student work.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Suggested steps. Money stays in code (`lab8.tools.compute_compensation`).

1. Open the store. Read the claim through `get_claim_view` (not SELECT *).
2. Missing order_id -> status `needs_info`. Do not write the ledger.
3. `lookup_order`. If not visible -> `escalated`. Do not copy phone, address, item, internal note.
4. Quote from the order row. Ignore delay numbers written in the ticket.
5. Quote amount 0 -> `denied`. Do not call issue_refund.
6. Quote amount > 0 -> `durability.issue_refund(conn, claim_id, <full quote>)`.
   Pass the FULL quote. The host checks the claim's own approval and subtracts
   what earlier claims already got for the same order (T13, T14). Do not
   subtract it yourself or the host subtracts twice.
   Auth failure or order already refunded -> `denied` (the host writes `policy_denied`).
   `proposal_amount` stays the full quote. Amount conflict -> `failed`.
7. Success -> `resolved`. One ledger row, one `refund_committed` audit.
8. Use MockLLM only to draft the reply text, if you want a model call at all.

The model must not choose the refund amount and must not commit the refund.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.

Group notes:

- Self-contained on purpose: the hidden grader copies only the three shape files
  (plus src/bonus/), so this file imports nothing from the other shapes.
- Trace records only: claim id + found/has_order_id flags, the allowlisted order
  fields returned by `lookup_order`, the quote computed by code, the host outcome,
  and the final decision. Never the ticket, the raw claim/order row, or str(exc).
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace

SHAPE = "workflow"


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))
    conn = connect(store_path)
    try:
        try:
            return _run(conn, claim_id, seed=seed, crash_at=crash_at, budget=budget, trace=trace)
        except InjectedCrash:
            # CP3: flush the trace, then let the injected crash propagate (T12, crash suite).
            trace.add("crash", {"at": crash_at})
            trace.write()
            raise
        except Exception as exc:  # run_claim must not raise; BaseException is not caught.
            reason = f"internal_error:{type(exc).__name__}"
            trace.add("error", {"reason": reason})  # type name only, never str(exc)
            return finish(
                conn,
                shape=SHAPE,
                claim_id=claim_id,
                seed=seed,
                status="failed",
                proposal_amount=0,
                budget=budget,
                trace=trace,
                error_reason=reason,
            )
    finally:
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
    budget: Budget,
    trace: Trace,
) -> RunResult:
    # 1. Claim through the allowlisted view (no parent_secret / raw headers).
    budget.add_tool(tool_cost())
    view = get_claim_view(conn, claim_id)
    trace.add(
        "claim",
        {"claim_id": claim_id, "found": bool(view.get("found")), "has_order_id": bool(view.get("order_id"))},
    )
    if not view.get("found"):
        return _exit(conn, claim_id, seed, budget, trace, status="failed", reason="unknown_claim", draft=False)

    # 2. No order_id -> needs_info. Never mine the ticket text for an order id.
    if not view.get("order_id"):
        return _exit(conn, claim_id, seed, budget, trace, status="needs_info", reason="missing_order_id")

    # 3. Order scoped to the claim's principal. lookup_order returns allowlisted fields only.
    budget.add_tool(tool_cost())
    order_view = lookup_order(conn, view["order_id"], view["principal_id"])
    order_event: dict[str, Any] = {"visible": bool(order_view.get("visible")), "reason": order_view.get("reason")}
    if order_view.get("visible"):
        order_event["order"] = dict(order_view["order"])
    trace.add("order", order_event)
    if not order_view.get("visible"):
        return _exit(conn, claim_id, seed, budget, trace, status="escalated", reason=order_view.get("reason"))

    # 4. Quote from the structured order row + current policy. Ticket numbers are ignored.
    budget.add_tool(tool_cost())
    quote = compute_compensation(conn, dict(order_view["order"]))
    trace.add(
        "quote",
        {
            "amount_vnd": int(quote["amount_vnd"]),
            "reason": quote["reason"],
            "clause_ids": list(quote["clause_ids"]),
            "parts": dict(quote["parts"]),
        },
    )

    # 5–7. Host gate.
    return _settle(conn, claim_id, seed, budget, trace, quote=quote, crash_at=crash_at)


def _settle(
    conn: sqlite3.Connection,
    claim_id: str,
    seed: int,
    budget: Budget,
    trace: Trace,
    *,
    quote: dict[str, Any],
    crash_at: str | None,
) -> RunResult:
    proposal = int(quote["amount_vnd"])

    # 5. Nothing owed -> denied without touching the host (so no policy_denied audit).
    if proposal <= 0:
        return _exit(conn, claim_id, seed, budget, trace, status="denied", reason=quote["reason"])

    # 6. FULL quote to the host. The host checks approval and subtracts earlier refunds
    #    on the same order. crash_at is forwarded; InjectedCrash is not caught here.
    trace.add("issue_refund", {"proposed_vnd": proposal})
    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    effect = outcome.get("effect") or {}
    trace.add(
        "host",
        {
            "ok": bool(outcome["ok"]),
            "reason": outcome["reason"],
            "conflict": bool(outcome["conflict"]),
            "amount_vnd": effect.get("amount_vnd"),
        },
    )

    # 7. Map the host outcome. proposal_amount stays the full quote on every branch.
    if outcome["ok"]:
        status, reason = "resolved", None
    elif outcome["conflict"]:
        status, reason = "failed", outcome["reason"]
    else:
        status, reason = "denied", outcome["reason"]
    return _exit(conn, claim_id, seed, budget, trace, status=status, reason=reason, proposal=proposal)


def _exit(
    conn: sqlite3.Connection,
    claim_id: str,
    seed: int,
    budget: Budget,
    trace: Trace,
    *,
    status: str,
    reason: str | None,
    proposal: int = 0,
    draft: bool = True,
) -> RunResult:
    trace.add("decision", {"status": status, "reason": reason, "proposal_amount": proposal})
    if draft:
        # 8. Only model call: draft reply text. The prompt holds the decision, not the ticket,
        #    and the output is not used for any decision.
        complete(budget, seed=seed, purpose="draft", prompt=f"status={status} proposal={proposal}")
    return finish(
        conn,
        shape=SHAPE,
        claim_id=claim_id,
        seed=seed,
        status=status,
        proposal_amount=proposal,
        budget=budget,
        trace=trace,
        error_reason=reason,
    )
