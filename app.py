from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os
import logging

# ----------------------------------------
#  ضبط مستوى تسجيل الـ logs لرؤية المخرجات أثناء التطوير
# ----------------------------------------
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ----------------------------------------
# 1. الإعداد: مفتاح Together AI ونقطة النهاية المعدَّلة
# ----------------------------------------
# تأكدي من تعيين المفتاح كمتغيّر بيئي باسم TOGETHER_AI_API_KEY

TOGETHER_AI_MODEL = "Qwen/Qwen2.5-72B-Instruct-Turbo"

# نقطة النهاية الصحيحة لإنشاء محادثة completion
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"

api_key = os.getenv("TOGETHER_AI_API_KEY")

# ----------------------------------------
# 2. دالة مساعدة للاتصال بـ Together AI بتنسيق Chat Completion
# ----------------------------------------
def generate_with_together(prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
    """
    ترسل طلبًا إلى Together AI للحصول على رد بناءً على الـ prompt.
    تستخدم تنسيق Chat Completion (model + messages).
    تعيد النص الذي يولّده Together AI أو رسالة خطأ مبسطة في حال الفشل.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }

    # تنسيق الطلب المطلوب
    payload = {
        "model": TOGETHER_AI_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "context_length_exceeded_behavior": "error"
    }

    response = requests.post(TOGETHER_API_URL, json=payload, headers=headers, timeout=30)
    if response.status_code != 200:
        logging.error(f"Together AI returned status {response.status_code}: {response.text}")
        return "عذراً، حدث خطأ أثناء محاولة إنشاء الرد الذكي، حاول مجدداً لاحقًا."

    data = response.json()
    # في تنسيق Chat Completion، الرد الفعلي يكون في choices[0]["message"]["content"]
    try:
        generated_text = data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Error parsing Together AI response: {e} | Response Body: {data}")
        return "عذراً، تعذّر فهم ردّ الذكاء الاصطناعي."
    return generated_text.strip()

# ----------------------------------------
# 3. بيانات مثال بسيطة (يمكن ربطها بقاعدة بيانات لاحقًا)
# ----------------------------------------
travel_packages = {
    "تركيا": [
        {"مدينة": "إسطنبول", "سعر": "500$", "نشاط": "جولة في البوسفور", "نوع الغرف": "مزدوجة", "عدد الأشخاص": 2},
        {"مدينة": "أنطاليا", "سعر": "400$", "نشاط": "زيارة الشلالات", "نوع الغرف": "فردية", "عدد الأشخاص": 1},
    ],
    "السعودية": [
        {"مدينة": "مكة", "سعر": "600$", "نشاط": "رحلة حج", "نوع الغرف": "ثلاثية", "عدد الأشخاص": 3},
        {"مدينة": "المدينة", "سعر": "550$", "نشاط": "زيارة المسجد النبوي", "نوع الغرف": "مزدوجة", "عدد الأشخاص": 2},
    ],
    "كابادوكيا": [
        {"مدينة": "كابادوكيا", "سعر": "450$", "نشاط": "ركوب المناطيد", "نوع الغرف": "مزدوجة", "عدد الأشخاص": 2},
        {"مدينة": "بورصة", "سعر": "350$", "نشاط": "زيارة جبل أولوداغ", "نوع الغرف": "فردية", "عدد الأشخاص": 1}
    ],
    "الإمارات": [
        {"مدينة": "دبي", "سعر": "700$", "نشاط": "زيارة برج خليفة", "نوع الغرف": "مزدوجة", "عدد الأشخاص": 2},
        {"مدينة": "أبوظبي", "سعر": "650$", "نشاط": "جولة في متحف اللوفر", "نوع الغرف": "فردية", "عدد الأشخاص": 1}
    ]
}

# ----------------------------------------
# 4. نقطة النهاية لاستقبال رسائل WhatsApp من Twilio
# ----------------------------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    # 4.1. استلام نص الرسالة الواردة من Twilio
    incoming = request.values.get("Body", "").strip()
    lower = incoming.lower()
    logging.info(f"Incoming message: {incoming}")

    # 4.2. نهيئ Response لـ Twilio
    resp = MessagingResponse()
    msg = resp.message()

    # 4.3. الردود السريعة بناءً على كلمات مفتاحية بسيطة
    greetings = ["مرحبا", "سلام", "أهلا", "hello", "hi"]
    if any(word in lower for word in greetings):
        msg.body("أهلاً! كيف يمكنني مساعدتك اليوم؟ يمكنك السؤال عن باقات السفر أو عن تفاصيل الوجهات.")
        return str(resp)

    if "باقات" in lower:
        msg.body("لدينا باقات سفر إلى: تركيا، السعودية، كابادوكيا، الإمارات. لأيّ وجهة تريد التفاصيل؟")
        return str(resp)

    for country in travel_packages:
        if country in lower:
            pkgs = travel_packages[country]
            text = f"باقات السفر إلى {country}:\n"
            for p in pkgs:
                text += (
                    f"- مدينة: {p['مدينة']}, سعر: {p['سعر']}, "
                    f"نشاط: {p['نشاط']}, غرف: {p['نوع الغرف']}, "
                    f"أشخاص: {p['عدد الأشخاص']}\n"
                )
            msg.body(text)
            return str(resp)

    # 4.4. إذا لم تنطبق أي ردود سريعة، ننتقل إلى Together AI لتوليد الرد الذكي
    prompt = (
        f"أنت مساعد حجز متقدم لوكالة سفر. المستخدم كتب: \"{incoming}\". "
        "أجب بصيغة عربية مبسطة وواضحة، وإذا سأله عن باقات قدم له معلومات، "
        "وإذا كان طلبه عامًّا يمكنك طلب توضيح أكثر."
    )

    try:
        ai_reply = generate_with_together(prompt, max_tokens=256, temperature=0.7)
    except Exception as e:
        logging.error(f"Error calling Together AI: {e}")
        ai_reply = "عذراً، حدثت مشكلة أثناء الاتصال بخدمة الذكاء الاصطناعي. حاولِ مجددًا لاحقًا."

    msg.body(ai_reply)
    return str(resp)

# ----------------------------------------
# 5. نقطة البداية لتشغيل Flask
# ----------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
