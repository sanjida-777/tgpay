from flask import Flask, render_template, request, jsonify
import requests
import os, json

app = Flask(__name__)

# Telegram Bot Credentials
BOT_TOKEN = "6477272802:AAFiO2Z9LGPXnmNLu-alkXqn-lQanQblZoM"
PROVIDER_TOKEN = "6073714100:TEST:TG_OBqaSK8xDn4xEZBq7AQ16N8A"  # Replace with your Stars provider token
ITEM_NAME = "Premium Item"
ITEM_PRICE = 1  # 1 Star

CURRENCY = "XTR"  # Replace with actual Telegram currency


# ✅ Store user payments (Format: { user_id: payment_id })
PAYMENT_RECORDS = {}
# ✅ Store refunded payments (Format: { user_id: refund_id })
REFUNDED_PAYMENTS = {}

# ✅ Home Route: Display the store page
@app.route("/")
def home():
    return render_template("index.html", item_name=ITEM_NAME, item_price=ITEM_PRICE)

# ✅ Payment Route: Handles payment request
@app.route("/pay", methods=["POST"])
def pay():
    data = request.json
    user_id = str(data.get("user_id"))  # Convert to string for consistency
    if not user_id:
        return jsonify({"error": "User ID required"}), 400

    # Create an invoice payload
    payload = {
        "chat_id": user_id,
        "title": ITEM_NAME,
        "description": "Exclusive item available for 1 Telegram Star!",
        "payload": f"user_{user_id}_payment",
        "provider_token": PROVIDER_TOKEN,
        "currency": CURRENCY,
        "prices": [{"label": ITEM_NAME, "amount": ITEM_PRICE}],  # Amount in smallest units
        "start_parameter": "start",
        "provider_data": json.dumps({})
    }

    response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice", json=payload)
    
    try:
        response_data = response.json()
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("🔹 Received Webhook Data:", json.dumps(data, indent=2))  # Debugging log

    # ✅ Handle Successful Payment
    if "message" in data and "successful_payment" in data["message"]:
        successful_payment = data["message"]["successful_payment"]
        chat_id = str(data["message"]["chat"]["id"])
        payment_id = successful_payment["telegram_payment_charge_id"]

        # Store the payment record
        PAYMENT_RECORDS[chat_id] = payment_id
        print(f"💰 Payment Successful! Stored Payment ID: {payment_id}")

        # Send a confirmation message
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": "✅ Thank you! Your item has been delivered."
        })

    # ✅ Handle Refund Notifications from Telegram
    if "message" in data and "refunded_payment" in data["message"]:
        refunded_payment = data["message"]["refunded_payment"]
        chat_id = str(data["message"]["chat"]["id"])
        refund_id = refunded_payment["telegram_payment_charge_id"]

        # Verify if this payment was originally recorded
        if chat_id in PAYMENT_RECORDS and PAYMENT_RECORDS[chat_id] == refund_id:
            REFUNDED_PAYMENTS[chat_id] = refund_id  # Store the refund record
            print(f"🔄 Refund received! Payment ID: {refund_id}")

            # Notify the user
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
                "chat_id": chat_id,
                "text": "🔄 Your payment has been refunded successfully. Your Stars should be back in your balance soon!"
            })
        else:
            print(f"⚠️ Refund received for unknown or mismatched payment: {refund_id}")

    return jsonify({"status": "ok"})

# ✅ Refund Route (for testing)
@app.route("/refund", methods=["POST"])
def refund():
    data = request.json
    user_id = str(data.get("user_id"))

    if not user_id:
        return jsonify({"error": "User ID required"}), 400

    # Check if the user has a valid payment
    if user_id not in PAYMENT_RECORDS:
        return jsonify({"error": "No valid payment found for refund"}), 400

    payment_id = PAYMENT_RECORDS[user_id]  # Get the transaction ID

    # Log the refund request
    print(f"🔄 Refund requested for User ID: {user_id}, Payment ID: {payment_id}")

    return jsonify({"message": "Refund request recorded. Wait for Telegram to process it.", "payment_id": payment_id})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
