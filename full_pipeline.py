"""
FULL PIPELINE: propose -> validate -> execute -> audit

Now with timing instrumentation per stage, and a trace_id that ties
every stage of one run together in the audit log.
"""

import time
from propose import propose_upsell
from attack_discount import propose_upsell_attack
from validate import validate_proposal
from execute import execute_approved_upsell
from audit import log_decision, new_trace_id


def run_full_pipeline(cart_items, use_attack=False):
    trace_id = new_trace_id()
    t_start = time.perf_counter()

    print("=" * 60)
    print(f"TRACE: {trace_id} | CART: {cart_items} | MODE:", "ATTACK" if use_attack else "NORMAL")
    print("=" * 60)

    # STAGE 1: PROPOSE
    t0 = time.perf_counter()
    proposal = propose_upsell_attack(cart_items) if use_attack else propose_upsell(cart_items)
    t_propose = (time.perf_counter() - t0) * 1000
    print("\n[1] PROPOSED:", proposal)
    print(f"    (propose took {t_propose:.1f}ms)")

    # STAGE 2: VALIDATE
    t0 = time.perf_counter()
    gate_result = validate_proposal(proposal, cart_items)
    t_validate = (time.perf_counter() - t0) * 1000
    print("\n[2] GATE DECISION:", gate_result)
    print(f"    (validate took {t_validate:.2f}ms)")

    # STAGE 3: EXECUTE (only if approved)
    exec_result = None
    t_execute = 0
    if gate_result["approved"]:
        t0 = time.perf_counter()
        exec_result = execute_approved_upsell(gate_result)
        t_execute = (time.perf_counter() - t0) * 1000
        print("\n[3] EXECUTED:", exec_result)
        print(f"    (execute took {t_execute:.1f}ms)")
        if exec_result["executed"]:
            print(f"\n✅ Real order created: {exec_result['order']['id']}")
        else:
            print(f"\n⚠️  Execution failed: {exec_result['reason']}")
    else:
        print("\n[3] EXECUTE: SKIPPED - gate blocked this proposal, no order created")
        print(f"   Reason: {gate_result['reason']}")

    t_total = (time.perf_counter() - t_start) * 1000

    latency = {
        "propose_ms": round(t_propose, 1),
        "validate_ms": round(t_validate, 2),
        "execute_ms": round(t_execute, 1),
        "total": round(t_total, 1),
    }

    # STAGE 4: AUDIT (always runs)
    log_decision(
        trace_id=trace_id,
        cart_items=cart_items,
        proposal=proposal,
        gate_result=gate_result,
        exec_result=exec_result,
        mode="attack" if use_attack else "normal",
        latency_ms=latency,
    )
    print(f"\n[4] AUDIT: logged | validate_ms={latency['validate_ms']} | total_ms={latency['total']}")
    print("=" * 60)

    return {"trace_id": trace_id, "gate_result": gate_result, "latency": latency}


if __name__ == "__main__":
    test_cart = [{"id": "sku_004", "quantity": 1}]  # phone case

    print("\n\n########## RUN 1: NORMAL AGENT ##########\n")
    run_full_pipeline(test_cart, use_attack=False)

    print("\n\n########## RUN 2: ADVERSARIAL AGENT ##########\n")
    run_full_pipeline(test_cart, use_attack=True)