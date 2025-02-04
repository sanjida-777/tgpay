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

# ✅ Home Route: Display the store page
@app.route("/")
def home():
    return render_template("index.html", item_name=ITEM_NAME, item_price=ITEM_PRICE)

# ✅ Payment Route: Handles payment request
@app.route("/pay", methods=["POST"])
def pay():
    data = request.json
    user_id = data.get("user_id")  # Extract Telegram user ID
    if not user_id:
        return jsonify({"error": "User ID required"}), 400

    # Create an invoice payload
    payload = {
        "chat_id": user_id,
        "title": ITEM_NAME,
        "description": "Exclusive item available for 1 Telegram Star!",
        "payload": "unique_payload",
        "provider_token": PROVIDER_TOKEN,
        "currency": CURRENCY,
        "prices": [{"label": ITEM_NAME, "amount": ITEM_PRICE}],  # Amount in smallest units
        "start_parameter": "start",
        "provider_data": json.dumps({})  # ✅ Correctly formatted empty JSON
    }

    response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice", json=payload)
    
    try:
        response_data = response.json()
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Webhook Route: Handles Telegram payment confirmation
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("🔹 Received Webhook Data:", json.dumps(data, indent=2))  # Debugging log

    # ✅ Handle Pre-Checkout Query (MUST be answered within 10 seconds)
    if "pre_checkout_query" in data:
        pre_checkout_id = data["pre_checkout_query"]["id"]
        
        # 🛠️ First, immediately approve the payment
        response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", json={
            "pre_checkout_query_id": pre_checkout_id,
            "ok": True
        })

        print("✅ Pre-checkout query approved!")

    # ✅ Handle Successful Payment
    if "message" in data and "successful_payment" in data["message"]:
        print("💰 Payment Successful:", json.dumps(data["message"]["successful_payment"], indent=2))
        chat_id = data["message"]["chat"]["id"]

        # Send a confirmation message to the user
        response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": "✅ Thank you! Your item has been delivered."
        })

    return jsonify({"status": "ok"})

# ✅ Start Flask Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
