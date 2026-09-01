"""
Step 0: Just check the Razorpay connection works.
Creates one test order for ₹500 and prints the response.
"""

import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not KEY_ID or not KEY_SECRET:
    raise SystemExit("Missing RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET in your .env file")

client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

# Razorpay amounts are in paise (smallest unit), so ₹500 = 50000
order = client.order.create({
    "amount": 50000,
    "currency": "INR",
    "receipt": "test_receipt_001",
    "notes": {
        "purpose": "connection test"
    }
})

print("Order created successfully:")
print(order)