"""
A tiny fake catalog for a merchant selling electronics accessories.
cost_price = what it costs the merchant to source the item
sell_price = normal selling price (before any upsell discount)
Margin = sell_price - cost_price. This is what the gate protects.
"""

CATALOG = [
    {
        "id": "sku_001",
        "name": "USB-C Fast Charger (20W)",
        "cost_price": 250,
        "sell_price": 499,
        "category": "charging"
    },
    {
        "id": "sku_002",
        "name": "USB-C Cable (1m, braided)",
        "cost_price": 80,
        "sell_price": 249,
        "category": "charging"
    },
    {
        "id": "sku_003",
        "name": "Wireless Earbuds (basic)",
        "cost_price": 600,
        "sell_price": 1299,
        "category": "audio"
    },
    {
        "id": "sku_004",
        "name": "Phone Case (clear, shockproof)",
        "cost_price": 90,
        "sell_price": 349,
        "category": "protection"
    },
    {
        "id": "sku_005",
        "name": "Screen Protector (tempered glass)",
        "cost_price": 40,
        "sell_price": 199,
        "category": "protection"
    },
    {
        "id": "sku_006",
        "name": "Power Bank (10000mAh)",
        "cost_price": 550,
        "sell_price": 999,
        "category": "charging"
    },
]


def get_catalog():
    return CATALOG


def get_item(sku_id):
    for item in CATALOG:
        if item["id"] == sku_id:
            return item
    return None