from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Telegram Bot Credentials
BOT_TOKEN = "6477272802:AAFiO2Z9LGPXnmNLu-alkXqn-lQanQblZoM"
PROVIDER_TOKEN = "6073714100:TEST:TG_OBqaSK8xDn4xEZBq7AQ16N8A"  # Replace with your Stars provider token
ITEM_NAME = "Premium Item"
ITEM_PRICE = 1  # 1 Star

@app.route("/")
def home():
    return render_template("index.html", item_name=ITEM_NAME, item_price=ITEM_PRICE)

@app.route("/pay", methods=["POST"])
def pay():
    data = request.json
    user_id = data.get("user_id")  # Telegram user ID
    if not user_id:
        return jsonify({"error": "User ID required"}), 400

    # Create an invoice
    payload = {
        "chat_id": user_id,
        "title": ITEM_NAME,
        "description": "Exclusive item available for 1 Telegram Star!",
        "payload": "unique_payload",
        "provider_token": PROVIDER_TOKEN,
        "currency": "XTR",
        "prices": [{"label": ITEM_NAME, "amount": ITEM_PRICE}],  # amount in smallest units
        "start_parameter": "start"
    }
    response = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendInvoice", json=payload)
    return jsonify(response.json())

@app.route("/success", methods=["POST"])
def success():
    data = request.json
    if "successful_payment" in data:
        return jsonify({"message": "Payment successful! Your item is delivered."})
    return jsonify({"error": "Invalid payment data"}), 400

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
