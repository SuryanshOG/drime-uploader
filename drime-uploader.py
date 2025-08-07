import streamlit as st
import requests
import os

st.set_page_config(page_title="Drime CDN Uploader", layout="centered")
st.title("🚀 Upload File to Drime from a CDN URL")

# Get Drime API token from secrets (or fallback to environment)
API_TOKEN = st.secrets.get("DRIME_API_TOKEN", os.getenv("DRIME_API_TOKEN"))
if not API_TOKEN:
    st.error("Missing Drime API token. Please set it in Streamlit secrets or environment.")
    st.stop()

# User input
cdn_url = st.text_input("Paste the direct CDN/download URL of the file")
upload_btn = st.button("Upload to Drime")

if upload_btn and cdn_url:
    filename = cdn_url.split("/")[-1]
    st.info(f"Downloading `{filename}`...")

    try:
        # Step 1: Download the file from CDN
        with requests.get(cdn_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        st.success(f"Downloaded `{filename}` successfully.")

        # Step 2: Upload to Drime
        st.info("Uploading to Drime...")
        with open(filename, 'rb') as file_data:
            headers = {"Authorization": f"Bearer {API_TOKEN}"}
            files = {'file': (filename, file_data)}
            upload_res = requests.post("https://app.drime.cloud/api/v1/uploads", headers=headers, files=files)

        if upload_res.status_code != 200:
            st.error(f"Upload failed: {upload_res.text}")
            os.remove(filename)
            st.stop()

        file_info = upload_res.json()
        entry_id = file_info.get("id")
        st.success("File uploaded to Drime successfully.")

        # Step 3: Create shareable link
        st.info("Creating shareable link...")
        link_res = requests.post(f"https://app.drime.cloud/api/v1/file-entries/{entry_id}/shareable-link", headers=headers)

        if link_res.status_code == 200:
            share_url = link_res.json().get("url")
            st.success("Shareable Link:")
            st.code(share_url)
        else:
            st.error(f"Failed to create shareable link: {link_res.text}")

        # Clean up
        os.remove(filename)

    except Exception as e:
        st.error(f"Something went wrong: {str(e)}")
