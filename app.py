import streamlit as st
import datetime
import csv
import os
import smtplib
from email.message import EmailMessage

st.set_page_config(page_title="Appointment Booking", layout="centered")

# CONFIGURE YOUR EMAIL CREDENTIALS HERE
SENDER_EMAIL = "sidinregina@gmail.com"
APP_PASSWORD = "gmdnghznftupisyx"

CSV_FILE = "appointments.csv"

# Initialize CSV if it doesn't exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Email", "Date", "Time", "Booked At"])

# Define time slots (9 AM to 5 PM, every hour)
def generate_time_slots():
    start = datetime.time(9, 0)
    end = datetime.time(17, 0)
    slots = []
    t = datetime.datetime.combine(datetime.date.today(), start)
    while t.time() < end:
        slots.append(t.time())
        t += datetime.timedelta(hours=0.5)
    return slots

# Get available slots for a specific date
def get_available_slots(selected_date):
    booked = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Date"] == str(selected_date):
                    booked.add(row["Time"])
    all_slots = generate_time_slots()
    return [slot for slot in all_slots if str(slot) not in booked]

def send_email(to_email, subject, message):
    try:
        email = EmailMessage()
        email["From"] = SENDER_EMAIL
        email["To"] = to_email
        email["Subject"] = subject
        email.set_content(message)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(email)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

# ---- UI ----
st.title("📅 Book Your Appointment")

with st.form("booking_form"):
    name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    date = st.date_input("Select Date", min_value=datetime.date.today())
    
    available_slots = get_available_slots(date)
    if available_slots:
        time = st.selectbox("Select Time", available_slots)
    else:
        time = None
        st.warning("No available time slots for this date. Please choose another day.")

    submitted = st.form_submit_button("Book Appointment")

    if submitted:
        if not time:
            st.error("Please select a valid time slot.")
        else:
            # Save to CSV
            with open(CSV_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([name, email, date, time, datetime.datetime.now()])

            # Send confirmation email
            message = (
                f"Hello {name},\n\n"
                f"Your appointment is confirmed for {date} at {time}.\n\n"
                "Thank you!"
            )
            if send_email(email, "Appointment Confirmation", message):
                st.success(f"✅ Thank you, {name}! Appointment booked and confirmation email sent.")
# ----- Admin Dashboard -----
st.sidebar.title("🔐 Admin Login")

admin_mode = st.sidebar.checkbox("Admin Mode")
admin_password = st.sidebar.text_input("Enter Admin Password", type="password")

if admin_mode and admin_password == "admin123":  # <-- Set your own password here
    st.header("📋 Admin Dashboard: All Bookings")

    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r") as file:
            reader = csv.reader(file)
            bookings = list(reader)

        if len(bookings) <= 1:
            st.info("No bookings found.")
        else:
            headers = bookings[0]
            data = bookings[1:]

            # Display bookings
            st.dataframe(data, use_container_width=True, hide_index=True)

            # Optional: Delete a booking
            st.subheader("🗑️ Delete a Booking")
            options = [f"{i+1}. {row[0]} - {row[2]} at {row[3]}" for i, row in enumerate(data)]
            selected = st.selectbox("Select a booking to delete", options)

            if st.button("Delete Selected Booking"):
                index_to_delete = options.index(selected)
                del data[index_to_delete]

                # Write back to CSV
                with open(CSV_FILE, "w", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(headers)
                    writer.writerows(data)

                st.success("✅ Booking deleted.")
                st.experimental_rerun()
else:
    if admin_mode:
        st.sidebar.error("❌ Incorrect password")
