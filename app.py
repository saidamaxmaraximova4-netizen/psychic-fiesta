
import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ["BOT_TOKEN"]
CHANNEL = os.environ["CHANNEL_ID"]
API = f"https://api.telegram.org/bot{TOKEN}"


def telegram(method, data):
    r = requests.post(
        f"{API}/{method}",
        json=data,
        timeout=15
    )
    r.raise_for_status()
    result = r.json()
    if not result.get("ok"):
        raise RuntimeError(result.get("description"))
    return result["result"]


def keyboard():
    return {
        "inline_keyboard": [
            [{
                "text": "📢 Quyon Bozor kanaliga obuna bo‘lish",
                "url": "https://t.me/" + CHANNEL.lstrip("@")
            }],
            [{
                "text": "✅ Obunani tekshirish",
                "callback_data": "check_sub"
            }]
        ]
    }


def send_message(chat_id, text, buttons=None):
    data = {"chat_id": chat_id, "text": text}
    if buttons:
        data["reply_markup"] = buttons
    telegram("sendMessage", data)


@app.get("/")
def home():
    return "Quyon Bozor bot ishlayapti!"


@app.post("/webhook")
def webhook():
    update = request.get_json(silent=True) or {}

    if "message" in update:
        msg = update["message"]
        if msg.get("text", "").startswith("/start"):
            send_message(
                msg["chat"]["id"],
                "🐇 Quyon Bozorga xush kelibsiz!\n"
                "Davom etish uchun kanalga obuna bo‘ling.",
                keyboard()
            )

    elif "callback_query" in update:
        q = update["callback_query"]

        telegram("answerCallbackQuery", {
            "callback_query_id": q["id"]
        })

        if q.get("data") == "check_sub":
            user_id = q["from"]["id"]
            member = telegram("getChatMember", {
                "chat_id": CHANNEL,
                "user_id": user_id
            })

            status = member["status"]
            joined = (
                status in ("creator", "administrator", "member")
                or (
                    status == "restricted"
                    and member.get("is_member", False)
                )
            )

            chat_id = q["message"]["chat"]["id"]

            if joined:
                send_message(
                    chat_id,
                    "✅ Obuna tasdiqlandi! Xush kelibsiz."
                )
            else:
                send_message(
                    chat_id,
                    "❌ Avval kanalga obuna bo‘ling, "
                    "keyin qayta tekshiring.",
                    keyboard()
                )

    return "OK", 200
