"""
STAGE 4: AUDIT (v2 - structured tracing)

Every decision gets a trace_id (like a real distributed tracing system),
latency measurements per stage, and a clear guardrail_status field.
This is what lets you say "every money action is fully auditable" with
actual evidence, not just a log line.
"""

import json
import os
import uuid
from datetime import datetime, timezone

LOG_FILE = "audit_log.jsonl"


def new_trace_id():
    """Short unique ID per pipeline run, like a real tracing system."""
    return f"trace_{uuid.uuid4().hex[:12]}"


def log_decision(
    trace_id,
    cart_items,
    proposal,
    gate_result,
    exec_result=None,
    mode="normal",
    latency_ms=None,
):
    """
    latency_ms: dict like {"propose": 812.3, "validate": 0.4, "execute": 340.1, "total": 1152.8}
    """
    if gate_result["approved"] and exec_result and exec_result["executed"]:
        guardrail_status = "PASSED_EXECUTED"
    elif gate_result["approved"] and exec_result and not exec_result["executed"]:
        guardrail_status = "PASSED_EXECUTION_FAILED"
    elif not gate_result["approved"]:
        guardrail_status = "BLOCKED"
    else:
        guardrail_status = "PASSED_NOT_EXECUTED"

    record = {
        "trace_id": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "cart": cart_items,
        "proposed": proposal,
        "gate_approved": gate_result["approved"],
        "decision_reasoning": gate_result["reason"],
        "guardrail_status": guardrail_status,
        "executed": exec_result["executed"] if exec_result else False,
        "order_id": (
            exec_result["order"]["id"]
            if exec_result and exec_result.get("order")
            else None
        ),
        "latency_ms": latency_ms or {},
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    return record


def read_audit_log():
    if not os.path.exists(LOG_FILE):
        return []
    records = []
    with open(LOG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def print_audit_summary():
    records = read_audit_log()
    if not records:
        print("No audit records yet.")
        return

    total = len(records)
    by_status = {}
    for r in records:
        s = r.get("guardrail_status", "UNKNOWN")
        by_status[s] = by_status.get(s, 0) + 1

    print(f"AUDIT SUMMARY: {total} total runs")
    for status, count in by_status.items():
        print(f"  {status}: {count}")
    print("-" * 70)
    for r in records:
        lat = r.get("latency_ms", {}).get("total", "?")
        print(f"[{r['trace_id']}] {r['guardrail_status']:25s} | {lat}ms | {r['decision_reasoning']}")


if __name__ == "__main__":
    print_audit_summary()