from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# Telegram Bot Credentials
BOT_TOKEN = "6477272802:AAFiO2Z9LGPXnmNLu-alkXqn-lQanQblZoM"
PROVIDER_TOKEN = "6073714100:TEST:TG_OBqaSK8xDn4xEZBq7AQ16N8A"  # Replace with your Stars provider token
ITEM_NAME = "Premium Item"
ITEM_PRICE = 1  # 1 Star

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
        "currency": "XTR",
        "prices": [{"label": ITEM_NAME, "amount": ITEM_PRICE }],  # Amount in smallest units
        "start_parameter": "start"
    }

    response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice", json=payload)
    return jsonify(response.json())

# ✅ Webhook Route: Handles Telegram payment confirmation
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Received Webhook Data:", data)  # Debugging log

    # 🔹 Handle Pre-Checkout (approve the payment)
    if "pre_checkout_query" in data:
        print("Pre-Checkout Query:", data["pre_checkout_query"])
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerPreCheckoutQuery", json={
            "pre_checkout_query_id": data["pre_checkout_query"]["id"],
            "ok": True
        })

    # 🔹 Handle Successful Payment
    if "successful_payment" in data.get("message", {}):
        print("Payment Successful:", data["message"]["successful_payment"])
        chat_id = data["message"]["chat"]["id"]
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={
            "chat_id": chat_id,
            "text": "✅ Thank you! Your item has been delivered."
        })

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
