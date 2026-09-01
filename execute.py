"""
STAGE 3: EXECUTE

This only runs AFTER the gate has approved a proposal. It takes the
approved item + final_price and actually creates a Razorpay test-mode
order for it - simulating the upsell item being added to checkout.

If the gate blocked the proposal, this stage never runs at all.
That's the whole point: nothing reaches Razorpay unless it's been validated.
"""

import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))


def execute_approved_upsell(gate_result):
    """
    gate_result: the dict returned by validate_proposal(), MUST have
                 approved == True. Creates a real Razorpay test-mode order
                 for the approved item at its final (possibly discounted) price.

    Returns a dict with the execution outcome.
    """
    if not gate_result.get("approved"):
        # Defensive check - execute should never be called on a blocked proposal,
        # but we guard against it anyway rather than trusting the caller.
        return {
            "executed": False,
            "reason": "Cannot execute - proposal was not approved by the gate",
            "order": None
        }

    item = gate_result["item"]
    final_price = gate_result["final_price"]

    # Razorpay needs amount in paise (smallest currency unit)
    amount_paise = int(round(final_price * 100))

    try:
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"upsell_{item['id']}",
            "notes": {
                "type": "upsell_order",
                "item_id": item["id"],
                "item_name": item["name"],
                "gate_reason": gate_result["reason"]
            }
        })
        return {
            "executed": True,
            "reason": "Order created successfully in Razorpay test-mode",
            "order": order
        }
    except Exception as e:
        return {
            "executed": False,
            "reason": f"Razorpay API error: {str(e)}",
            "order": None
        }


if __name__ == "__main__":
    # Quick manual test using a fake pre-approved gate result
    from catalog import get_item

    fake_approved_result = {
        "approved": True,
        "reason": "APPROVED: margin stays at 79.9%, within all limits",
        "item": get_item("sku_005"),
        "final_price": 199.0
    }

    print("Executing a pre-approved upsell...")
    result = execute_approved_upsell(fake_approved_result)
    print(result)