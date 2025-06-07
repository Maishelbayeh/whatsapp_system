import streamlit as st
import pandas as pd
import os
import json
from urllib.parse import urlencode, parse_qs

# Parse query parameters from the URL
params = st.experimental_get_query_params()
def_val = lambda k, default: params.get(k, [default])[0]
destination   = def_val("destination", "")
travel_date   = def_val("date", "")
passengers    = int(def_val("passengers", "1"))
room_type     = def_val("room_type", "")

st.title("Travel Booking System")

# 1) Editable fields for all collected info
st.header("Booking Details (You can edit)")
destination = st.text_input("Destination", value=destination)
travel_date = st.text_input("Travel Date", value=travel_date)
passengers = st.number_input("Number of Passengers", min_value=1, value=passengers, step=1)
room_type = st.text_input("Room Type", value=room_type)

# 2) Collect info for each passenger
data = []
st.header("Passenger Information")
for i in range(passengers):
    st.subheader(f"Passenger {i+1}")
    name = st.text_input(f"Name for passenger {i+1}", key=f"name_{i}")
    passport_number = st.text_input(f"Passport Number for passenger {i+1}", key=f"passport_{i}")
    file = st.file_uploader(f"Passport Image for passenger {i+1}", type=["png","jpg","jpeg"], key=f"file_{i}")
    data.append({
        "name": name,
        "passport_number": passport_number,
        "file": file
    })

# 3) Submit button
if st.button("Submit"):
    # تحقق من أن جميع الحقول ممتلئة
    errors = []
    for idx, d in enumerate(data):
        if not d["name"] or not d["passport_number"] or not d["file"]:
            errors.append(f"Please complete all fields for passenger {idx+1}.")
    if not destination or not travel_date or not room_type:
        errors.append("Please complete all booking details fields.")
    if errors:
        for e in errors:
            st.error(e)
    else:
        # حفظ الصور وبيانات المسافرين
        os.makedirs("data/passports", exist_ok=True)
        passengers_list = []
        for idx, d in enumerate(data):
            file_details = None
            if d["file"]:
                file_details = f"{d['passport_number']}_{d['name']}_{d['file'].name}"
                with open(os.path.join("data/passports", file_details), "wb") as f:
                    f.write(d["file"].getbuffer())
            passengers_list.append({
                "name": d["name"],
                "passport_number": d["passport_number"],
                "file": file_details
            })
        # حفظ كل بيانات الرحلة والمسافرين
        submission = {
            "destination": destination,
            "date": travel_date,
            "room_type": room_type,
            "passengers": passengers_list
        }
        os.makedirs("data", exist_ok=True)
        path = os.path.join("data", "submissions.json")
        if os.path.exists(path):
            with open(path, "r+", encoding="utf-8") as f:
                try:
                    all_data = json.load(f)
                except Exception:
                    all_data = []
                all_data.append(submission)
                f.seek(0)
                json.dump(all_data, f, ensure_ascii=False, indent=2)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([submission], f, ensure_ascii=False, indent=2)
        st.success("Information for all passengers submitted successfully!")
