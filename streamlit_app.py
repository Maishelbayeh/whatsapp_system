# user_form.py
import streamlit as st

# Title of the app
st.title("Travel Booking System")

# Section for end users
st.header("User Information")

# Collecting user details
name = st.text_input("Name")
passport_number = st.text_input("Passport Number")
number_of_people = st.number_input("Number of People", min_value=1, step=1)

# Upload passport images
passport_images = st.file_uploader("Upload Passport Images", accept_multiple_files=True)

# Button to submit information
if st.button("Submit"):
    st.success("Information submitted successfully!")

# business_dashboard.py
