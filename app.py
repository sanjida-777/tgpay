from flask import Flask, render_template, request, jsonify
import requests
import os, json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

# Telegram Bot Credentials
BOT_TOKEN = "6477272802:AAFiO2Z9LGPXnmNLu-alkXqn-lQanQblZoM"
PROVIDER_TOKEN = "6073714100:TEST:TG_OBqaSK8xDn4xEZBq7AQ16N8A"  # Replace with your Stars provider token
ITEM_NAME = "Premium Item"
ITEM_PRICE = 1  # 1 Star

CURRENCY = "XTR"  # Example: "USD", "EUR", etc.

# Store user payments (Format: { user_id: payment_id })
PAYMENT_RECORDS = {}
# Store refunded payments (Format: { user_id: refund_id })
REFUNDED_PAYMENTS = {}

# Home Route: Display the store page
@app.route("/")
def home():
    return render_template("index.html", item_name=ITEM_NAME, item_price=ITEM_PRICE)

# Payment Route: Handles payment request
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

    # Send invoice to Telegram
    response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice", json=payload)
    
    try:
        response_data = response.json()
        if response_data.get('ok'):
            return jsonify(response_data)
        else:
            return jsonify({"error": "Error sending invoice", "message": response_data.get("description")}), 500
    except Exception as e:
        return jsonify({"error": "Failed to parse response", "message": str(e)}), 500

# Webhook to handle Telegram updates
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    with open("webhook_log.json", "a") as log_file:
        log_file.write(str(data) + "\n")  # ✅ Logs webhook data

    print("Received Webhook Data:", data)

    if "pre_checkout_query" in data:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", json={
            "pre_checkout_query_id": data["pre_checkout_query"]["id"],
            "ok": True
        })

    if "successful_payment" in data.get("message", {}):
        chat_id = data["message"]["chat"]["id"]
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": "✅ Payment received!"
        })

    return jsonify({"status": "ok"})


# Refund Route (for testing)
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


