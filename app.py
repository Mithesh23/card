import streamlit as st
import pandas as pd
import qrcode
import os
from PIL import Image, ImageDraw, ImageFont
import zipfile
import io
import shutil

# === Constants ===
FONT_PATH = "fonts/CodecPro-Regular.ttf"  # Update if different
TEMPLATE_PATH = "id_template.png"
QR_FOLDER = "temp_qrcodes"
CARD_FOLDER = "temp_cards"
PASSWORD = "swechasoai2025"  # Change to your desired password

# === Setup folders ===
os.makedirs(QR_FOLDER, exist_ok=True)
os.makedirs(CARD_FOLDER, exist_ok=True)

# === Wrap text ===
def wrap_text(text, font, max_width):
    lines = []
    words = text.split()
    line = ""
    dummy_img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy_img)

    for word in words:
        test_line = line + " " + word if line else word
        width = draw.textbbox((0, 0), test_line, font=font)[2]
        if width <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

# === Streamlit UI ===
st.set_page_config(page_title="ID Card Generator with QR", layout="centered")
st.title("🪪 ID Card Generator with QR Code")
st.write("Upload a CSV with columns: `Name`, `ID`, and `username`")

# === Password Protection ===
st.subheader("🔐 Authentication")
input_password = st.text_input("Enter password to generate ID cards", type="password")

if input_password != PASSWORD:
    st.warning("Please enter the correct password to proceed.")
    st.stop()

uploaded_file = st.file_uploader("📁 Upload CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Validate columns
    if not {'Name', 'ID', 'username'}.issubset(df.columns):
        st.error("❌ CSV must contain 'Name', 'ID', and 'username' columns.")
        st.stop()

    try:
        name_font = ImageFont.truetype(FONT_PATH, 35)
        id_font = ImageFont.truetype(FONT_PATH, 22)
    except:
        st.error("❌ Font file not found. Please make sure 'CodecPro-Regular.ttf' is in the 'fonts/' folder.")
        st.stop()

    # === Generate ===
    st.info("⏳ Generating cards...")
    base_url = "https://code.swecha.org/"
    name_x, name_y = 200, 510
    max_name_width = 500
    line_spacing = 45
    id_y_offset = 10
    qr_position = (250, 240)

    for _, row in df.iterrows():
        name = row["Name"]
        id_number = str(row["ID"])
        username = row["username"]
        profile_url = base_url + username

        # QR Generation
        qr_img = qrcode.make(profile_url)
        qr_path = os.path.join(QR_FOLDER, f"{id_number}.jpg")
        qr_img.save(qr_path)

        # Create ID Card
        template = Image.open(TEMPLATE_PATH).convert("RGB")
        draw = ImageDraw.Draw(template)

        # Draw wrapped name
        name_lines = wrap_text(name, name_font, max_name_width)
        for i, line in enumerate(name_lines):
            y = name_y + i * line_spacing
            draw.text((name_x, y), line, font=name_font, fill="black")

        # Draw ID
        id_y = name_y + len(name_lines) * line_spacing + id_y_offset
        draw.text((name_x, id_y), f"ID: {id_number}", font=id_font, fill="black")

        # Paste QR code
        qr_img_resized = Image.open(qr_path).resize((255, 255))
        template.paste(qr_img_resized, qr_position)

        # Save card
        output_filename = f"{name.replace(' ', '_')}_{id_number}.png"
        template.save(os.path.join(CARD_FOLDER, output_filename))

    # === Create ZIP for download ===
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for filename in os.listdir(CARD_FOLDER):
            file_path = os.path.join(CARD_FOLDER, filename)
            zipf.write(file_path, arcname=filename)
    zip_buffer.seek(0)

    st.success("✅ ID cards generated!")
    st.download_button("⬇️ Download All ID Cards (ZIP)", zip_buffer, file_name="ID_Cards.zip")

    # Clean up after download
    shutil.rmtree(QR_FOLDER)
    shutil.rmtree(CARD_FOLDER)
