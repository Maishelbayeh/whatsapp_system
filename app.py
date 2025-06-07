from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests, logging, os, re
from dateutil import parser as dateparser
from urllib.parse import urlencode
import time

# ----------------------------------------
# Setup & Configuration
# ----------------------------------------
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# Health-check so "/" doesn't 404
@app.route("/", methods=["GET","POST"])
def index():
    return "WhatsApp Booking Bot is running!", 200

# In-memory session store (use Redis/DB in prod)
sessions = {}

# Streamlit form URL
STREAMLIT_BASE_URL = "https://whatsappsystem-n8g9tebqrpvddqyluvjp8y.streamlit.app/"

# Together AI config
API_KEY           = "dd7a6fc277c9ee36419a087740614213725230ad625445de90711fc0862400ad"
TOGETHER_AI_MODEL = "Qwen/Qwen2.5-72B-Instruct-Turbo"
TOGETHER_API_URL  = "https://api.together.xyz/v1/chat/completions"

# Predefined travel packages
travel_packages = {
    "تركيا": [
        {
            "مدينة": "إسطنبول",
            "سعر": "500$",
            "نشاط": "جولة في البوسفور",
            "فنادق": [
                {
                    "اسم": "فندق البوسفور",
                    "غرف": [
                        {"نوع": "مفردة", "سعر": "100$"},
                        {"نوع": "مزدوجة", "سعر": "150$"},
                        {"نوع": "ثلاثية", "سعر": "200$"}
                    ]
                },
                {
                    "اسم": "فندق تقسيم",
                    "غرف": [
                        {"نوع": "مفردة", "سعر": "120$"},
                        {"نوع": "مزدوجة", "سعر": "170$"}
                    ]
                }
            ],
            "رحلات": [
                {"اسم": "جولة في البوسفور", "سعر": "50$"},
                {"اسم": "زيارة متحف آيا صوفيا", "سعر": "30$"}
            ]
        },
        {
            "مدينة": "أنطاليا",
            "سعر": "400$",
            "نشاط": "زيارة الشلالات",
            "فنادق": [
                {
                    "اسم": "فندق الشاطئ",
                    "غرف": [
                        {"نوع": "مفردة", "سعر": "90$"},
                        {"نوع": "مزدوجة", "سعر": "140$"}
                    ]
                },
                {
                    "اسم": "منتجع أنطاليا",
                    "غرف": [
                        {"نوع": "مزدوجة", "سعر": "160$"},
                        {"نوع": "ثلاثية", "سعر": "210$"}
                    ]
                }
            ],
            "رحلات": [
                {"اسم": "جولة شلالات دودان", "سعر": "40$"},
                {"اسم": "جولة في البلدة القديمة", "سعر": "35$"}
            ]
        }
    ],
    "السعودية": [
        {
            "مدينة": "مكة",
            "سعر": "600$",
            "نشاط": "رحلة حج",
            "فنادق": [
                {
                    "اسم": "فندق أبراج مكة",
                    "غرف": [
                        {"نوع": "مفردة", "سعر": "200$"},
                        {"نوع": "مزدوجة", "سعر": "300$"}
                    ]
                },
                {
                    "اسم": "فندق الصفوة",
                    "غرف": [
                        {"نوع": "مزدوجة", "سعر": "320$"},
                        {"نوع": "ثلاثية", "سعر": "400$"}
                    ]
                }
            ],
            "رحلات": [
                {"اسم": "زيارة المسجد الحرام", "سعر": "مجانية"},
                {"اسم": "جولة جبل النور", "سعر": "25$"}
            ]
        },
        {
            "مدينة": "المدينة",
            "سعر": "550$",
            "نشاط": "زيارة المسجد النبوي",
            "فنادق": [
                {
                    "اسم": "فندق دار الإيمان",
                    "غرف": [
                        {"نوع": "مفردة", "سعر": "180$"},
                        {"نوع": "مزدوجة", "سعر": "250$"}
                    ]
                },
                {
                    "اسم": "فندق المدينة موفنبيك",
                    "غرف": [
                        {"نوع": "مزدوجة", "سعر": "270$"},
                        {"نوع": "ثلاثية", "سعر": "350$"}
                    ]
                }
            ],
            "رحلات": [
                {"اسم": "زيارة المسجد النبوي", "سعر": "مجانية"},
                {"اسم": "جولة جبل أحد", "سعر": "20$"}
            ]
        }
    ],
    "كابادوكيا": [
        {
            "مدينة": "كابادوكيا",
            "سعر": "450$",
            "نشاط": "ركوب المناطيد",
            "فنادق": [
                {
                    "اسم": "فندق الكهف",
                    "غرف": [
                        {"نوع": "مفردة", "سعر": "110$"},
                        {"نوع": "مزدوجة", "سعر": "160$"}
                    ]
                },
                {
                    "اسم": "فندق الصخور",
                    "غرف": [
                        {"نوع": "مزدوجة", "سعر": "170$"},
                        {"نوع": "ثلاثية", "سعر": "220$"}
                    ]
                }
            ],
            "رحلات": [
                {"اسم": "جولة مناطيد الصباح", "سعر": "60$"},
                {"اسم": "جولة الكهوف", "سعر": "30$"}
            ]
        },
        {
            "مدينة": "بورصة",
            "سعر": "350$",
            "نشاط": "زيارة جبل أولوداغ",
            "فنادق": [
                {
                    "اسم": "فندق أولوداغ",
                    "غرف": [
                        {"نوع": "مفردة", "سعر": "100$"},
                        {"نوع": "مزدوجة", "سعر": "140$"}
                    ]
                },
                {
                    "اسم": "منتجع بورصة",
                    "غرف": [
                        {"نوع": "مزدوجة", "سعر": "160$"},
                        {"نوع": "ثلاثية", "سعر": "210$"}
                    ]
                }
            ],
            "رحلات": [
                {"اسم": "جولة جبل أولوداغ", "سعر": "40$"},
                {"اسم": "جولة الأسواق القديمة", "سعر": "25$"}
            ]
        }
    ],
    "الإمارات": [
        {
            "مدينة": "دبي",
            "سعر": "700$",
            "نشاط": "زيارة برج خليفة",
            "فنادق": [
                {
                    "اسم": "فندق العنوان",
                    "غرف": [
                        {"نوع": "مفردة", "سعر": "200$"},
                        {"نوع": "مزدوجة", "سعر": "300$"}
                    ]
                },
                {
                    "اسم": "فندق جميرا",
                    "غرف": [
                        {"نوع": "مزدوجة", "سعر": "320$"},
                        {"نوع": "ثلاثية", "سعر": "400$"}
                    ]
                }
            ],
            "رحلات": [
                {"اسم": "زيارة برج خليفة", "سعر": "60$"},
                {"اسم": "جولة في دبي مول", "سعر": "30$"}
            ]
        },
        {
            "مدينة": "أبوظبي",
            "سعر": "650$",
            "نشاط": "جولة في متحف اللوفر",
            "فنادق": [
                {
                    "اسم": "فندق قصر الإمارات",
                    "غرف": [
                        {"نوع": "مفردة", "سعر": "180$"},
                        {"نوع": "مزدوجة", "سعر": "250$"}
                    ]
                },
                {
                    "اسم": "فندق روتانا",
                    "غرف": [
                        {"نوع": "مزدوجة", "سعر": "270$"},
                        {"نوع": "ثلاثية", "سعر": "350$"}
                    ]
                }
            ],
            "رحلات": [
                {"اسم": "زيارة متحف اللوفر", "سعر": "50$"},
                {"اسم": "جولة في الكورنيش", "سعر": "20$"}
            ]
        }
    ]
}
DESTINATIONS = list(travel_packages.keys())
ROOM_TYPES   = ["فردية","مزدوجة","ثلاثية"]

# ----------------------------------------
# Fallback to Together AI
# ----------------------------------------
def generate_with_together(prompt, max_tokens=512, temperature=0.7):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    payload = {
        "model": TOGETHER_AI_MODEL,
        "messages": [{"role":"user","content":prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "context_length_exceeded_behavior":"error"
    }
    resp = requests.post(TOGETHER_API_URL, json=payload, headers=headers, timeout=30)
    if resp.status_code != 200:
        logging.error(f"Together AI error {resp.status_code}: {resp.text}")
        return "عذراً، لا أستطيع توليد رد ذكي الآن. حاول لاحقاً."
    data = resp.json()
    return data.get("choices",[{}])[0].get("message",{}).get("content","عذراً، لم أفهم طلبك تماماً.").strip()

# ----------------------------------------
# Slot-extraction helpers
# ----------------------------------------
def extract_destination(text):
    return next((d for d in DESTINATIONS if d in text), None)

def extract_date(text):
    m = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text)
    if m:
        try: return dateparser.parse(m.group(1), dayfirst=True).date().isoformat()
        except: pass
    try:
        dt = dateparser.parse(text, fuzzy=True)
        return dt.date().isoformat() if dt else None
    except:
        return None

def extract_integer(text):
    m = re.search(r'\b(\d+)\b', text)
    return int(m.group(1)) if m else None

def extract_room_type(text):
    return next((r for r in ROOM_TYPES if r in text), None)

# ----------------------------------------
# WhatsApp webhook
# ----------------------------------------
@app.route("/whatsapp", methods=["GET", "POST"])
def whatsapp_reply():
    if request.method == "GET":
        return "This endpoint is for WhatsApp webhook POST requests.", 200
    user    = request.values.get("From")
    incoming= request.values.get("Body","").strip().lower()
    logging.info(f"{user} → {incoming}")

    # إعداد الجلسة وسجل الحوار
    sess = sessions.setdefault(user, {})
    history = sess.setdefault("history", [])
    resp = MessagingResponse()
    msg  = resp.message()

    # أضف الرسالة الجديدة إلى سجل الحوار
    history.append({"role": "user", "content": incoming})

    # احذف الرسائل الأقدم من 20 دقيقة
    now = time.time()
    timestamps = sess.setdefault("timestamps", [])
    timestamps.append(now)
    # احذف الرسائل الأقدم من 20 دقيقة
    while timestamps and now - timestamps[0] > 1200:
        timestamps.pop(0)
        history.pop(0)

    # دالة توليد الرد الذكي مع سجل الحوار
    def smart_reply(prompt):
        # مرر سجل الحوار مع prompt جديد
        messages = history[-10:] + [{"role": "user", "content": prompt}]
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        payload = {
            "model": TOGETHER_AI_MODEL,
            "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            "max_tokens": 512,
            "temperature": 0.7,
            "context_length_exceeded_behavior": "error"
        }
        resp = requests.post(TOGETHER_API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            logging.error(f"Together AI error {resp.status_code}: {resp.text}")
            return "عذراً، لا أستطيع توليد رد ذكي الآن. حاول لاحقاً."
        data = resp.json()
        reply = data.get("choices",[{}])[0].get("message",{}).get("content","عذراً، لم أفهم طلبك تماماً.").strip()
        # أضف رد الذكاء الاصطناعي إلى سجل الحوار
        history.append({"role": "assistant", "content": reply})
        return reply

    # إذا اكتملت جميع الحقول الأساسية، أرسل رابط الفورم مباشرة
    if all(sess.get(k) for k in ["destination", "date", "passengers", "room_type"]):
        qs = urlencode(sess)
        link = STREAMLIT_BASE_URL + "?" + qs
        prompt = (
            f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
            f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
            f"رابط استكمال البيانات: {link}\n"
            "المطلوب: اشكر المستخدم وأرسل له الرابط ليستكمل بياناته ويرفع جواز السفر. أجب بالعربية فقط."
        )
        reply = smart_reply(prompt)
        print("AI reply:", reply)
        msg.body(reply)
        return str(resp)

    # كلمات تدل على رغبة المستخدم في استكمال الحجز أو الحصول على الرابط
    form_triggers = [
        "ارسل الرابط", "لينك", "اكمل", "تأكيد الحجز", "استكمال", "رابط الفورم", "تاكيد الحجز"
    ]

    # دوال مساعدة لصياغة سجل الحوار وملخص الحجز
    def get_history_text():
        lines = []
        for m in history[-10:]:
            role = "المستخدم" if m["role"] == "user" else "المساعد"
            lines.append(f"{role}: {m['content']}")
        return "\n".join(lines)

    def get_booking_summary():
        return (
            f"- الوجهة: {sess.get('destination', 'غير محددة')}\n"
            f"- التاريخ: {sess.get('date', 'غير محدد')}\n"
            f"- عدد المسافرين: {sess.get('passengers', 'غير محدد')}\n"
            f"- نوع الغرفة: {sess.get('room_type', 'غير محدد')}"
        )

    # 0) Greeting/Small-talk → AI
    if any(incoming.startswith(g) for g in ["مرحبا","أهلا","hi","hello","هاي"]):
        opts = "، ".join(DESTINATIONS)
        prompt = (
            f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
            f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
            f"البكجات المتوفرة حاليًا هي: {opts}.\n"
            "المطلوب: رحب بالمستخدم واطلب منه اختيار وجهة من البكجات المتوفرة. أجب بالعربية فقط."
        )
        reply = smart_reply(prompt)
        print("AI reply:", reply)
        msg.body(reply)
        return str(resp)

    # 1) "packages" → list destinations (ذكي)
    if any(k in incoming for k in ["بكج","باكج","باقات","package"]):
        opts = "، ".join(DESTINATIONS)
        prompt = (
            f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
            f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
            f"البكجات المتوفرة حاليًا هي: {opts}.\n"
            "المطلوب: أطلب من المستخدم اختيار وجهة ليحصل على التفاصيل. أجب بالعربية فقط."
        )
        reply = smart_reply(prompt)
        print("AI reply:", reply)
        msg.body(reply)
        return str(resp)

    # 2) Country-specific packages (ذكي)
    for c, pkgs in travel_packages.items():
        if c in incoming:
            details = ""
            for p in pkgs:
                details += f"- {p['مدينة']} ({p['سعر']}): {p['نشاط']}\n"
            prompt = (
                f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
                f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
                f"تفاصيل البكجات إلى {c}:\n{details}"
                "المطلوب: أطلب من المستخدم اختيار مدينة أو المتابعة بالحجز. أجب بالعربية فقط."
            )
            reply = smart_reply(prompt)
            print("AI reply:", reply)
            msg.body(reply)
            return str(resp)

    # 3) Slot-filling: destination (ذكي)
    if "destination" not in sess:
        d = extract_destination(incoming)
        if d:
            sess["destination"] = d
            prompt = (
                f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
                f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
                "المطلوب: أطلب من المستخدم إدخال تاريخ السفر. أجب بالعربية فقط."
            )
            reply = smart_reply(prompt)
            print("AI reply:", reply)
            msg.body(reply)
        else:
            opts = "، ".join(DESTINATIONS)
            prompt = (
                f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
                f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
                f"البكجات المتوفرة حاليًا هي: {opts}.\n"
                "المطلوب: أطلب من المستخدم اختيار وجهة من البكجات المتوفرة. أجب بالعربية فقط."
            )
            reply = smart_reply(prompt)
            print("AI reply:", reply)
            msg.body(reply)
        return str(resp)

    # 4) Slot-filling: date (ذكي)
    if "date" not in sess:
        dt = extract_date(incoming)
        if dt:
            sess["date"] = dt
            prompt = (
                f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
                f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
                "المطلوب: أطلب من المستخدم عدد المسافرين. أجب بالعربية فقط."
            )
            reply = smart_reply(prompt)
            print("AI reply:", reply)
            msg.body(reply)
        else:
            prompt = (
                f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
                f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
                "المطلوب: أطلب من المستخدم إدخال تاريخ السفر (مثلاً 25/06/2025 أو غدًا). أجب بالعربية فقط."
            )
            reply = smart_reply(prompt)
            print("AI reply:", reply)
            msg.body(reply)
        return str(resp)

    # 5) Slot-filling: passengers (ذكي)
    if "passengers" not in sess:
        n = extract_integer(incoming)
        if n:
            sess["passengers"] = n
            prompt = (
                f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
                f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
                "المطلوب: أطلب من المستخدم نوع الغرفة (فردية، مزدوجة، ثلاثية أو أكثر من نوع). أجب بالعربية فقط."
            )
            reply = smart_reply(prompt)
            print("AI reply:", reply)
            msg.body(reply)
        else:
            prompt = (
                f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
                f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
                "المطلوب: أطلب من المستخدم إدخال عدد المسافرين (مثال: 3). أجب بالعربية فقط."
            )
            reply = smart_reply(prompt)
            print("AI reply:", reply)
            msg.body(reply)
        return str(resp)

    # 6) Slot-filling: room type (ذكي)
    if "room_type" not in sess:
        # عدل التعرف ليقبل صيغ مركبة
        rt = extract_room_type(incoming)
        if not rt:
            # جرب استخراج أي نوع غرفة من النص (حتى لو مركب)
            found_types = [r for r in ROOM_TYPES if r in incoming]
            if found_types:
                rt = " و ".join(found_types)
        if rt:
            sess["room_type"] = rt
            qs = urlencode(sess)
            link = STREAMLIT_BASE_URL + "?" + qs
            prompt = (
                f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
                f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
                f"رابط استكمال البيانات: {link}\n"
                "المطلوب: اشكر المستخدم وأرسل له الرابط ليستكمل بياناته ويرفع جواز السفر. أجب بالعربية فقط."
            )
            reply = smart_reply(prompt)
            print("AI reply:", reply)
            msg.body(reply)
        else:
            prompt = (
                f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
                f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
                "المطلوب: أطلب من المستخدم اختيار نوع الغرفة (فردية، مزدوجة، ثلاثية أو أكثر من نوع). أجب بالعربية فقط."
            )
            reply = smart_reply(prompt)
            print("AI reply:", reply)
            msg.body(reply)
        return str(resp)

    # 7) Final fallback → AI
    opts = "، ".join(DESTINATIONS)
    prompt = (
        f"سجل الحوار حتى الآن:\n{get_history_text()}\n"
        f"ملخص حالة الحجز:\n{get_booking_summary()}\n"
        f"البكجات المتوفرة حاليًا هي: {opts}.\n"
        "المطلوب: ساعد المستخدم في الحجز أو الاستفسار عن البكجات الحقيقية فقط. أجب بالعربية فقط."
    )
    reply = smart_reply(prompt)
    print("AI reply:", reply)
    msg.body(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
