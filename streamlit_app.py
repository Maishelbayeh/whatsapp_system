import streamlit as st
import pandas as pd
import os
import json
from urllib.parse import urlencode, parse_qs

# Parse query parameters from the URL
params = st.experimental_get_query_params()
destination   = params.get("destination", [""])[0]
travel_date   = params.get("date",        [""])[0]
passengers    = int(params.get("passengers", ["1"])[0])
room_type     = params.get("room_type",  [""])[0]

st.title("Travel Booking System")

# 1) Show the details we already collected via WhatsApp
st.header("Booking Details")
st.markdown(f"- **Destination:** {destination}")
st.markdown(f"- **Travel Date:** {travel_date}")
st.markdown(f"- **Number of Passengers:** {passengers}")
st.markdown(f"- **Room Type:** {room_type}")

# 2) Collect personal info
st.header("User Information")
name             = st.text_input("Name")
passport_number  = st.text_input("Passport Number")

# 3) Upload exactly N passport photos
st.subheader("Passport Photos")
files = st.file_uploader(
    f"Upload {passengers} passport image(s)",
    type=["png","jpg","jpeg"],
    accept_multiple_files=True
)
if files:
    if len(files) != passengers:
        st.warning(f"Please upload exactly {passengers} file(s).")
    else:
        st.success(f"{len(files)} files selected.")

# 4) Submit button
if st.button("Submit"):
    if not name or not passport_number:
        st.error("Please enter your name and passport number.")
    elif not files or len(files) != passengers:
        st.error(f"You must upload exactly {passengers} passport image(s).")
    else:
        # Save submission to JSON
        submission = {
            "destination": destination,
            "date": travel_date,
            "passengers": passengers,
            "room_type": room_type,
            "name": name,
            "passport_number": passport_number,
            "files": [f.name for f in files]
        }
        os.makedirs("data", exist_ok=True)
        path = os.path.join("data", "submissions.json")
        if os.path.exists(path):
            with open(path, "r+", encoding="utf-8") as f:
                data = json.load(f)
                data.append(submission)
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([submission], f, ensure_ascii=False, indent=2)

        st.success("Information submitted successfully!")
