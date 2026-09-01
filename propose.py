"""
STAGE 1: PROPOSE

The agent looks at what's in the customer's cart and proposes ONE
upsell/cross-sell item from the catalog, with an optional discount.

Important: this stage does NOT check if the proposal is safe.
It just proposes. The gate (validate.py, built next) is what checks it.
This separation is the whole point of the architecture.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv
from catalog import get_catalog

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an upsell agent for an e-commerce checkout.
Given the customer's cart and the full product catalog, propose ONE additional
item the customer might want to add, to increase order value.

You may optionally propose a discount (as a percentage, 0-100) to make the
offer more attractive. Only propose a discount if you think it meaningfully
helps close the upsell — don't discount by default.

Respond ONLY with valid JSON, no other text, in this exact shape:
{
  "proposed_item_id": "sku_xxx",
  "discount_percent": 0,
  "reasoning": "one sentence on why this item fits the cart"
}
"""


def propose_upsell(cart_items):
    """
    cart_items: list of dicts, each like {"id": "sku_001", "quantity": 1}
    Returns the raw proposal dict from the LLM (UNVALIDATED).
    """
    catalog = get_catalog()

    user_prompt = f"""
Customer's current cart:
{json.dumps(cart_items, indent=2)}

Full product catalog available to upsell from:
{json.dumps(catalog, indent=2)}

Propose one upsell item now.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
    )

    raw_text = response.choices[0].message.content.strip()

    try:
        proposal = json.loads(raw_text)
    except json.JSONDecodeError:
        # LLM didn't return clean JSON - treat as a failed proposal
        proposal = {
            "proposed_item_id": None,
            "discount_percent": 0,
            "reasoning": f"PARSE_ERROR: {raw_text}"
        }

    return proposal


if __name__ == "__main__":
    # Quick manual test: customer bought a phone case, what does it propose?
    test_cart = [{"id": "sku_004", "quantity": 1}]
    result = propose_upsell(test_cart)
    print("Raw proposal from agent:")
    print(json.dumps(result, indent=2))