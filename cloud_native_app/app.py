import streamlit as st
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv #to access the environmental variables from .env file
from supabase import create_client, Client #connecting with supabase database and id_photo policies created for cloud private photo saving
import qrcode
from PIL import Image
import io
import cv2 # OpenCV for QR code reading

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# --- CONFIGURATION ---
# Load environment variables from .env file
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(url, key)

# Define the name of your storage bucket
STORAGE_BUCKET_NAME = "id_photos"

@st.cache_data(ttl=10)
def fetch_id_cards(search=None):
    query = supabase.table("id_cards").select("*").order("created_at", desc=True)
    if search:
        query = query.or_(f"full_name.ilike.%{search}%,rrn.ilike.%{search}%")
    return query.execute().data


@st.cache_data(ttl=10)
def fetch_verified_ids():
    rows = supabase.table("verifications").select("card_id").execute().data
    return {r["card_id"] for r in rows}


@st.cache_data(ttl=300)
def get_signed_photo_url(photo_path):
    if not photo_path:
        return None
    return supabase.storage.from_(STORAGE_BUCKET_NAME)\
        .create_signed_url(photo_path, 300)["signedURL"]

# --- HELPER FUNCTIONS ---
def generate_qr_code(data: str) -> Image:
    """Generates a QR code image from the given data."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def decode_qr_code(image_bytes) -> str:
    """Decodes a QR code from image bytes and returns the data."""
    try:
        # Save the uploaded file bytes to a temporary file to be read by OpenCV
        with open("temp_qr.png", "wb") as f:
            f.write(image_bytes.getbuffer())
        
        # Read and decode
        img = cv2.imread("temp_qr.png")
        detector = cv2.QRCodeDetector()
        data, bbox, straight_qrcode = detector.detectAndDecode(img)
        
        # Clean up the temporary file
        os.remove("temp_qr.png")

        return data if data else None
    except Exception as e:
        st.error(f"Could not decode QR code. Error: {e}")
        return None

def send_qr_email(recipient_email: str, recipient_name: str, qr_image_bytes: bytes):
    """Constructs and sends an email with the QR code attached."""
    try:
        # Get email credentials from environment variables
        sender_email = os.environ.get("EMAIL_SENDER")
        sender_password = os.environ.get("EMAIL_PASSWORD")

        if not all([sender_email, sender_password]):
            st.error("Email credentials are not set in the environment. Cannot send email.")
            return

        # Create the email message
        msg = MIMEMultipart()
        msg['Subject'] = "Your New Digital ID Card QR Code"
        msg['From'] = sender_email
        msg['To'] = recipient_email

        # Create the HTML body of the email
        html_body = f"""
        <html>
        <body>
            <h2>Hello {recipient_name},</h2>
            <p>Welcome! Your digital ID card has been successfully created.</p>
            <p>Please find your unique QR code attached to this email. You can present this code for verification.</p>
            <br>
            <p>Thank you,</p>
            <p><b>Cloud ID Management System</b></p>
        </body>
        </html>
        """
        
        # Attach the HTML body to the message
        msg.attach(MIMEText(html_body, 'html'))

        # Attach the QR code image
        image = MIMEImage(qr_image_bytes, name=f"{recipient_name}_qr.png")
        msg.attach(image)

        # Connect to the SMTP server (Gmail example) and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True # Indicate success
    except Exception as e:
        st.error(f"Failed to send email. Error: {e}")
        return False # Indicate failure

# --- UI PAGES ---

def process_verification(card_uuid: str):
    """
    Handles the core logic of verifying an ID after a UUID is extracted.
    This function validates, fetches, displays, and logs the verification attempt.
    """
    if not card_uuid:
        st.error("Could not read a valid ID from the QR code.")
        supabase.table("verifications").insert({
            "result": "failed_decode", "note": "Could not read QR code from the provided image."
        }).execute()
        return

    # Validate QR code content format
    try:
        uuid.UUID(card_uuid)
    except ValueError:
        st.error("Invalid QR Code Format.")
        st.warning("This QR code was not generated by our system.")
        supabase.table("verifications").insert({
            "result": "failed_invalid_format",
            "note": f"Scanned invalid QR data: {card_uuid}"
        }).execute()
        return

    # Fetch data from Supabase
    try:
        with st.spinner("Fetching data from the cloud..."):
            query = supabase.table("id_cards").select("*").eq("id", card_uuid).execute()

            if not query.data:
                st.error("ID Card Not Found!")
                st.warning(f"The ID `{card_uuid}` does not exist in the database.")
                supabase.table("verifications").insert({
                    "result": "failed_not_found",
                    "note": f"Attempted verification with non-existent ID: {card_uuid}"
                }).execute()
                return

            card_data = query.data[0]
            photo_path = card_data.get("photo_path")
            signed_url_response = supabase.storage.from_(STORAGE_BUCKET_NAME).create_signed_url(photo_path, 60)
            photo_url = signed_url_response['signedURL']

            st.success("Verification Successful!")

            col1, col2 = st.columns(2)
            with col1:
                st.image(photo_url, caption="ID Photo", width=250)
            with col2:
                st.subheader(card_data['full_name'])
                st.text(f"RRN: {card_data.get('rrn', 'N/A')}")
                st.text(f"Department: {card_data['department']}")
                st.text(f"Email: {card_data['email']}")
                st.text(f"Phone: {card_data['phone']}")
                status = "ACTIVE" if card_data['is_active'] else "REVOKED"
                if card_data['is_active']:
                    st.success(f"Status: {status}")
                else:
                    st.error(f"Status: {status}")

            supabase.table("verifications").insert({
                "card_id": card_uuid, "result": "success"
            }).execute()

    except Exception as e:
        st.error(f"An error occurred: {e}")
        # Check if card_uuid is a valid UUID before trying to log it as a foreign key
        try:
            uuid.UUID(card_uuid)
            log_data = {"card_id": card_uuid, "result": "error", "note": str(e)}
        except ValueError:
            log_data = {"result": "error", "note": f"Error with invalid UUID {card_uuid}: {str(e)}"}
        supabase.table("verifications").insert(log_data).execute()

def create_id_page():
    st.header("Create New ID Card")
    st.write("Fill in the details below and capture a live photo.")

    # --- FORM (NO CAMERA INSIDE) ---
    with st.form("new_id_form"):
        full_name = st.text_input("Full Name")
        rrn = st.text_input("RRN (Registration Number)")
        department = st.text_input("Department")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email Address")

        submitted = st.form_submit_button("Create ID Card")

    # --- CAMERA (OUTSIDE FORM – INSTANT LOAD) ---
    st.subheader("Capture Photo")
    activate_camera = st.checkbox("Turn On Camera to Capture Photo", key="cam_toggle")

    img_file_buffer = None
    if activate_camera:
        img_file_buffer = st.camera_input("Smile!", key="photo_camera")

    # --- SUBMIT LOGIC (UNCHANGED) ---
    if submitted:
        if not all([full_name, rrn, department, phone, email, img_file_buffer]):
            st.error("Please fill out all fields and capture a photo.")
            return

        query = supabase.table("id_cards").select("id")\
            .or_(f"email.eq.{email},phone.eq.{phone},rrn.eq.{rrn}").execute()
        if query.data:
            st.warning("An ID card with this email, phone number, or RRN already exists.")
            return

        unique_filename = f"{uuid.uuid4()}.jpg"
        file_path_for_storage = f"photos/{unique_filename}"
        img_bytes = img_file_buffer.getvalue()

        supabase.storage.from_(STORAGE_BUCKET_NAME).upload(
            file=img_bytes,
            path=file_path_for_storage,
            file_options={"content-type": "image/jpeg"}
        )

        insert_data = {
            "full_name": full_name,
            "rrn": rrn,
            "department": department,
            "phone": phone,
            "email": email,
            "photo_path": file_path_for_storage,
            "is_active": True
        }

        data = supabase.table("id_cards").insert(insert_data).execute().data
        card_uuid = data[0]["id"]

        qr_img = generate_qr_code(card_uuid)
        buf = io.BytesIO()
        qr_img.save(buf, format="PNG")

        send_qr_email(email, full_name, buf.getvalue())

        st.success("🎉 ID Card Created Successfully!")
        st.image(buf.getvalue())


def verify_id_page():
    """Page for verifying an ID card by either uploading or scanning a QR code."""
    st.header("Verify ID Card")
    st.write("You can either upload a QR code image or scan it directly using your camera.")

    tab1, tab2 = st.tabs(["⬆Upload QR Code", "📸 Scan with Camera"])

    with tab1:
        uploaded_file = st.file_uploader(
            "Choose a QR code image",
            type=['png', 'jpg', 'jpeg'],
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            card_uuid = decode_qr_code(uploaded_file)
            process_verification(card_uuid)

    with tab2:
        st.info("Position the QR code in front of the camera and take a picture.")
        
        # --- START OF FIX: Add a checkbox to control the camera ---
        activate_scanner = st.checkbox("Turn On Camera to Scan QR Code")
        
        if activate_scanner:
            camera_image_buffer = st.camera_input(
                "Scan QR Code",
                key="qr_camera_scanner",
                label_visibility="collapsed"
            )
            if camera_image_buffer is not None:
                card_uuid = decode_qr_code(camera_image_buffer)
                process_verification(card_uuid)

def admin_panel_page():
    st.header("Admin Panel")
    st.write("Live database editor and analytics dashboard")

    # --- METRICS (CACHED) ---
    total_ids = supabase.table("id_cards").select("id", count="exact").execute().count
    total_verified = supabase.table("verifications").select("id", count="exact").execute().count

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registered", total_ids)
    col2.metric("Total Verified", total_verified)
    col3.metric("Remaining", total_ids - total_verified)

    st.divider()

    # --- SEARCH ---
    search = st.text_input("Search by Name or RRN")

    data = fetch_id_cards(search)
    if not data:
        st.info("No records found.")
        return

    verified_ids = fetch_verified_ids()

    # --- LIVE VERIFICATION MONITOR ---
    st.subheader("Live Verification Monitor")

    col_v, col_p = st.columns(2)

    with col_v:
        st.markdown("### ✅ Verified")
        for r in data:
            if r["id"] in verified_ids:
                st.write(f"{r['full_name']} | {r['rrn']}")

    with col_p:
        st.markdown("### ⏳ Not Verified")
        for r in data:
            if r["id"] not in verified_ids:
                st.write(f"{r['full_name']} | {r['rrn']}")

    st.divider()

    # --- EDIT RECORDS ---
    st.subheader("Edit ID Records")

    for row in data:
        with st.expander(f"{row['full_name']} | {row['rrn']}"):

            photo_url = get_signed_photo_url(row.get("photo_path"))
            if photo_url:
                st.image(photo_url, width=150, caption="ID Photo")

            full_name = st.text_input("Full Name", row["full_name"], key=f"name_{row['id']}")
            department = st.text_input("Department", row["department"], key=f"dept_{row['id']}")
            phone = st.text_input("Phone", row["phone"], key=f"phone_{row['id']}")
            email = st.text_input("Email", row["email"], key=f"email_{row['id']}")
            is_active = st.checkbox("Active", row["is_active"], key=f"active_{row['id']}")

            col_u, col_d = st.columns(2)

            # --- UPDATE (NO RERUN) ---
            if col_u.button("Update", key=f"update_{row['id']}"):
                supabase.table("id_cards").update({
                    "full_name": full_name,
                    "department": department,
                    "phone": phone,
                    "email": email,
                    "is_active": is_active,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", row["id"]).execute()

                st.success("Updated")
                fetch_id_cards.clear()
                fetch_verified_ids.clear()
                get_signed_photo_url.clear()

            # --- DELETE ---
            if col_d.button("Delete", key=f"delete_{row['id']}"):
                supabase.table("id_cards").delete().eq("id", row["id"]).execute()

                st.warning("Deleted")
                fetch_id_cards.clear()
                fetch_verified_ids.clear()
                get_signed_photo_url.clear()

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="Cloud ID System", layout="centered")
    st.title("Cloud-Based ID Management System")

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Create ID", "Verify ID", "Admin Panel"])

    if page == "Create ID":
        create_id_page()
    elif page == "Verify ID":
        verify_id_page()
    elif page == "Admin Panel":
        admin_panel_page()

if __name__ == "__main__":
    main()