"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        budget = Budget()
        trace = Trace(make_run_id("single", claim_id, seed))

        def decide(observation: dict) -> dict:
            last_tool = observation.get("last_tool")
            result = observation.get("last_result") or {}
            if last_tool == "get_claim_view":
                trace.add(
                    "claim_view",
                    {key: result[key] for key in ("found", "claim_id", "order_id") if key in result},
                )
                if not result.get("found"):
                    return {"final": {"status": "failed", "error_reason": "unknown_claim"}}
                if not result.get("order_id"):
                    return {"final": {"status": "needs_info", "error_reason": "missing_order_id"}}
                return {
                    "tool": "lookup_order",
                    "args": {
                        "order_id": result["order_id"],
                        "principal_id": result["principal_id"],
                    },
                }
            if last_tool == "lookup_order":
                trace.add("order", result)
                if not result.get("visible"):
                    status = (
                        "needs_info"
                        if result.get("reason") == "missing_order_id"
                        else "escalated"
                    )
                    return {"final": {"status": status, "error_reason": result.get("reason")}}
                return {"tool": "compute_compensation", "args": {"order": result["order"]}}
            if last_tool == "compute_compensation":
                trace.add("quote", result)
                amount = int(result["amount_vnd"])
                return {
                    "final": {
                        "status": "denied" if amount <= 0 else "quoted",
                        "proposal_amount": amount,
                        "error_reason": result.get("reason") if amount <= 0 else None,
                    }
                }
            return {
                "tool": "get_claim_view",
                "args": {"claim_id": observation["claim"]["claim_id"]},
            }

        reaction = run_react(
            conn,
            budget,
            observation={"claim": {"claim_id": claim_id}},
            decide=decide,
            max_steps=8,
        )
        final = reaction["final"]
        status = final.get("status", "failed")
        proposal = int(final.get("proposal_amount", 0))
        error_reason = final.get("error_reason")
        if reaction["stopped"] == "step_cap":
            status = "failed"
            proposal = 0
            error_reason = "step_cap"
            trace.add("decision", {"status": status, "reason": error_reason})
        elif status == "quoted":
            outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
            if not outcome["ok"]:
                status = "failed" if outcome["conflict"] else "denied"
                error_reason = outcome["reason"]
            else:
                status = "resolved"
                error_reason = None
        complete(budget, seed=seed, purpose="draft", prompt=status)
        trace.add("decision", {"status": status, "reason": error_reason})
        return finish(
            conn,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )
    finally:
        conn.close()
