from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import logging
import re
from dateutil import parser as dateparser
from urllib.parse import urlencode

# ----------------------------------------
# Setup
# ----------------------------------------
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# In-memory session store (for demo; use Redis or a database in production)
sessions = {}

# Your Streamlit form base URL
STREAMLIT_BASE_URL = "https://your-streamlit-app-url/user_form"

# Predefined destinations
DESTINATIONS = ["تركيا", "السعودية", "كابادوكيا", "الإمارات"]

# Room types
ROOM_TYPES = ["فردية", "مزدوجة", "ثلاثية"]

# Helper functions
def extract_destination(text):
    for dest in DESTINATIONS:
        if dest in text:
            return dest
    return None

def extract_date(text):
    # attempt to find a date in DD/MM/YYYY or YYYY-MM-DD or natural language
    # first try explicit patterns
    m = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
    if m:
        try:
            return dateparser.parse(m.group(1), dayfirst=True).date().isoformat()
        except:
            pass
    # fallback to dateparser
    try:
        dt = dateparser.parse(text, fuzzy=True)
        if dt:
            return dt.date().isoformat()
    except:
        pass
    return None

def extract_integer(text):
    m = re.search(r'\b(\d+)\b', text)
    return int(m.group(1)) if m else None

def extract_room_type(text):
    for rt in ROOM_TYPES:
        if rt in text:
            return rt
    return None

# ----------------------------------------
# WhatsApp webhook endpoint
# ----------------------------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    from_number = request.values.get("From")
    incoming = request.values.get("Body", "").strip().lower()
    logging.info(f"{from_number} → {incoming}")

    # get or create session
    user_sess = sessions.setdefault(from_number, {})

    resp = MessagingResponse()
    msg = resp.message()

    # step 1: destination
    if "destination" not in user_sess:
        dest = extract_destination(incoming)
        if dest:
            user_sess["destination"] = dest
            msg.body(f"أين تود السفر؟ لقد اخترت {dest}. متى تريد الانطلاق؟ (مثلاً 25/06/2025)")
        else:
            msg.body("إلى أي وجهة تريد السفر؟ (مثلاً تركيا، السعودية، كابادوكيا، الإمارات)")
        return str(resp)

    # step 2: date
    if "date" not in user_sess:
        travel_date = extract_date(incoming)
        if travel_date:
            user_sess["date"] = travel_date
            msg.body(f"حسناً، تاريخ السفر: {travel_date}. كم عدد المسافرين؟")
        else:
            msg.body("ليس واضحًا. من فضلك ادخل تاريخ السفر (مثلاً 25/06/2025 أو غدًا).")
        return str(resp)

    # step 3: passengers
    if "passengers" not in user_sess:
        num = extract_integer(incoming)
        if num:
            user_sess["passengers"] = num
            msg.body(f"عدد المسافرين: {num}. ما نوع الغرف التي تريدها؟ (فردية، مزدوجة، ثلاثية)")
        else:
            msg.body("كم عدد المسافرين معك؟ ارسل رقمًا مثال: 3")
        return str(resp)

    # step 4: room type
    if "room_type" not in user_sess:
        rt = extract_room_type(incoming)
        if rt:
            user_sess["room_type"] = rt
            # all slots collected → generate form link
            params = {
                "destination": user_sess["destination"],
                "date": user_sess["date"],
                "passengers": user_sess["passengers"],
                "room_type": user_sess["room_type"]
            }
            form_url = f"{STREAMLIT_BASE_URL}?{urlencode(params)}"
            msg.body(
                f"عظيم! لإكمال بياناتك، استخدم هذا الرابط:\n{form_url}\n"
                "بعد الإرسال، سأخبر الوكالة لإتمام الحجز."
            )
        else:
            msg.body("ما نوع الغرف؟ اختر من: فردية، مزدوجة، ثلاثية")
        return str(resp)

    # fallback — should not reach here
    msg.body("عذراً، حدث خطأ. لنبدأ مجددًا: إلى أي وجهة تريد السفر؟")
    sessions.pop(from_number, None)
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
