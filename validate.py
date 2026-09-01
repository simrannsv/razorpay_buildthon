"""
STAGE 2: VALIDATE (the gate)

This checks the agent's proposal from propose.py against HARD, CODE-ENFORCED
rules. The LLM's opinion doesn't matter here - these checks run no matter
what the agent "wanted" to do.

This is the core of your project: the agent can propose anything,
but only proposals that pass EVERY rule here are allowed through.
"""

from catalog import get_item

# --- Hard rules (tune these numbers as you like) ---
#Margin--is the profit percent
MIN_MARGIN_PERCENT = 20     # after any discount, margin must stay above this %
MAX_DISCOUNT_PERCENT = 30   # never allow a discount bigger than this, ever


def validate_proposal(proposal, cart_items):
    """
    proposal: the dict from propose_upsell() - e.g.
        {"proposed_item_id": "sku_005", "discount_percent": 0, "reasoning": "..."}
    cart_items: the customer's current cart (used to check for duplicates)

    Returns a dict:
        {
            "approved": True/False,
            "reason": "why it was approved or blocked",
            "item": the catalog item if approved, else None,
            "final_price": price after discount, if approved
        }
    """
    item_id = proposal.get("proposed_item_id")
    discount = proposal.get("discount_percent", 0)

    # RULE 1: item must actually exist in the catalog (catches hallucination)
    item = get_item(item_id)
    if item is None:
        return {
            "approved": False,
            "reason": f"BLOCKED: proposed item '{item_id}' does not exist in catalog",
            "item": None,
            "final_price": None
        }

    # RULE 2: discount must be a sane number
    if not isinstance(discount, (int, float)) or discount < 0:
        return {
            "approved": False,
            "reason": f"BLOCKED: invalid discount value '{discount}'",
            "item": None,
            "final_price": None
        }

    # RULE 3: discount can never exceed the hard ceiling
    if discount > MAX_DISCOUNT_PERCENT:
        return {
            "approved": False,
            "reason": f"BLOCKED: discount {discount}% exceeds max allowed {MAX_DISCOUNT_PERCENT}%",
            "item": None,
            "final_price": None
        }

    # RULE 4: don't upsell something already in the cart
    cart_ids = [c["id"] for c in cart_items]
    if item_id in cart_ids:
        return {
            "approved": False,
            "reason": f"BLOCKED: '{item['name']}' is already in the cart",
            "item": None,
            "final_price": None
        }

    # RULE 5: margin check - the real money-safety rule
    final_price = item["sell_price"] * (1 - discount / 100)
    margin_amount = final_price - item["cost_price"]
    margin_percent = (margin_amount / final_price) * 100 if final_price > 0 else -100

    if margin_percent < MIN_MARGIN_PERCENT:
        return {
            "approved": False,
            "reason": (
                f"BLOCKED: margin would drop to {margin_percent:.1f}% "
                f"(minimum allowed is {MIN_MARGIN_PERCENT}%) at {discount}% discount"
            ),
            "item": None,
            "final_price": None
        }

    # All rules passed
    return {
        "approved": True,
        "reason": f"APPROVED: margin stays at {margin_percent:.1f}%, within all limits",
        "item": item,
        "final_price": round(final_price, 2)
    }


if __name__ == "__main__":
    # Manual tests to see the gate in action

    test_cart = [{"id": "sku_004", "quantity": 1}]  # phone case in cart

    print("--- Test 1: reasonable proposal (should APPROVE) ---")
    good_proposal = {
        "proposed_item_id": "sku_005",
        "discount_percent": 10,
        "reasoning": "test"
    }
    print(validate_proposal(good_proposal, test_cart))

    print("\n--- Test 2: discount too high (should BLOCK) ---")
    bad_discount = {
        "proposed_item_id": "sku_005",
        "discount_percent": 80,
        "reasoning": "test"
    }
    print(validate_proposal(bad_discount, test_cart))

    print("\n--- Test 3: hallucinated item (should BLOCK) ---")
    fake_item = {
        "proposed_item_id": "sku_999",
        "discount_percent": 0,
        "reasoning": "test"
    }
    print(validate_proposal(fake_item, test_cart))

    print("\n--- Test 4: item already in cart (should BLOCK) ---")
    duplicate = {
        "proposed_item_id": "sku_004",
        "discount_percent": 0,
        "reasoning": "test"
    }
    print(validate_proposal(duplicate, test_cart))