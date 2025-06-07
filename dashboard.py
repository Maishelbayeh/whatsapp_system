import streamlit as st
import pandas as pd

# Title of the app
st.title("Business Owner Dashboard")

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

# streamlit_app.py
# This file is now empty as the content has been moved to user_form.py and business_dashboard.py 