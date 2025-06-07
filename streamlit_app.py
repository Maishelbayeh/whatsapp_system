import streamlit as st
import pandas as pd

# Title of the app
st.title("Travel Booking System")

# Section to collect user information
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

# Section for dashboard
st.header("Booking Dashboard")

# Example data for dashboard
booking_data = {
    "Destination": ["Turkey", "Saudi Arabia"],
    "Bookings via AI": [10, 5],
    "Direct Bookings": [7, 8]
}

# Create a DataFrame
booking_df = pd.DataFrame(booking_data)

# Display the data as a table
st.table(booking_df)

# Display a bar chart
st.bar_chart(booking_df.set_index("Destination")) 