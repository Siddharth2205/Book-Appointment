import streamlit as st
import streamlit_authenticator as stauth
import datetime
import csv
import os
import smtplib
from email.message import EmailMessage

# -------------------- AUTHENTICATION --------------------

# Hashed passwords for users
hashed_passwords = stauth.Hasher(['test123', 'admin123']).generate()

credentials = {
    "usernames": {
        "sid": {
            "name": "Siddharth Modi",
            "password": hashed_passwords[0],
            "email": "sid@example.com"
        },
        "admin": {
            "name": "Admin",
            "password": hashed_passwords[1],
            "email": "admin@example.com"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "appt_cookie", "random_signature_key", cookie_expiry_days=30
)

# -------------------- LOGIN UI --------------------

name, authentication_status, username = authenticator.login("Login", "sidebar")

if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"👋 Welcome, {name}!")

    # -------------------- EMAIL CONFIG --------------------
    SENDER_EMAIL = st.secrets["email"]["sender"]
    APP_PASSWORD = st.secrets["email"]["password"]

    # -------------------- SETUP --------------------
    CSV_FILE = "appointments.csv"
    st.set_page_config(page_title="Appointment Booking", layout="centered")

    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Email", "Date", "Time", "Booked At"])

    # -------------------- FUNCTIONS --------------------

    def generate_time_slots():
        start = datetime.time(9, 0)
        end = datetime.time(17, 0)
        slots = []
        t = datetime.datetime.combine(datetime.date.today(), start)
        while t.time() < end:
            slots.append(t.time())
            t += datetime.timedelta(minutes=30)
        return slots

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
            st.error(f"📧 Failed to send email: {e}")
            return False

    # -------------------- MAIN UI --------------------
    st.title("📅 Book Your Appointment")
    st.markdown(f"👤 Logged in as: `{username}`")

    with st.form("booking_form"):
        name_input = st.text_input("Full Name", value=name)
        email = credentials["usernames"][username]["email"]
        date = st.date_input("Select Date", min_value=datetime.date.today())
        available_slots = get_available_slots(date)

        if available_slots:
            time = st.selectbox("Select Time", available_slots)
        else:
            time = None
            st.warning("❌ No available time slots for this date. Please choose another day.")

        submitted = st.form_submit_button("Book Appointment")

        if submitted:
            if not time:
                st.error("❗ Please select a valid time slot.")
            else:
                with open(CSV_FILE, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([name_input, email, date, time, datetime.datetime.now()])

                message = (
                    f"Hello {name_input},\n\n"
                    f"Your appointment is confirmed for {date} at {time}.\n\n"
                    "Thank you!"
                )
                if send_email(email, "Appointment Confirmation", message):
                    st.success(f"✅ Appointment booked and confirmation email sent to {email}")

    # -------------------- ADMIN DASHBOARD --------------------
    st.sidebar.title("🛠 Admin Dashboard")
    if username == "admin":
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
                st.dataframe(data, use_container_width=True, hide_index=True)

                # Delete booking
                st.subheader("🗑️ Delete a Booking")
                options = [f"{i+1}. {row[0]} - {row[2]} at {row[3]}" for i, row in enumerate(data)]
                selected = st.selectbox("Select a booking to delete", options)

                if st.button("Delete Selected Booking"):
                    index_to_delete = options.index(selected)
                    del data[index_to_delete]

                    with open(CSV_FILE, "w", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerow(headers)
                        writer.writerows(data)

                    st.success("✅ Booking deleted.")
                    st.experimental_rerun()

else:
    if authentication_status is False:
        st.error("❌ Invalid username or password")
    elif authentication_status is None:
        st.warning("👆 Please enter your credentials")

