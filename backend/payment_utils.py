import razorpay
import os

# Razorpay Configuration
# Replace these with your actual keys or use environment variables
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder_id")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "placeholder_secret")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_razorpay_order(amount_in_inr: float, receipt_id: str):
    """
    Creates a Razorpay order.
    Amount should be in INR (automatically converted to paise).
    """
    data = {
        "amount": int(amount_in_inr * 100),  # amount in paise
        "currency": "INR",
        "receipt": receipt_id,
        "payment_capture": 1  # auto capture
    }
    order = client.order.create(data=data)
    return order

def verify_payment_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str):
    """
    Verifies the Razorpay payment signature.
    Returns True if valid, False otherwise.
    """
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }
    try:
        client.utility.verify_payment_signature(params_dict)
        return True
    except Exception:
        return False
