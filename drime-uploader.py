import streamlit as st
import requests
import os
import mimetypes

st.set_page_config(page_title="Drime CDN Uploader", layout="centered")
st.title("🚀 Upload File to Drime from a CDN URL")

# 🔐 Get Drime API token
API_TOKEN = st.secrets.get("DRIME_API_TOKEN", os.getenv("DRIME_API_TOKEN"))
if not API_TOKEN:
    st.error("❌ Missing Drime API token. Set it in Streamlit secrets or as an environment variable.")
    st.stop()

# 🌐 Input from user
cdn_url = st.text_input("Paste the direct CDN/download URL of the file")

if st.button("Upload to Drime") and cdn_url:
    filename = cdn_url.split("/")[-1]
    headers = {"Authorization": f"Bearer {API_TOKEN}"}

    try:
        # Step 1: Download the file
        st.info(f"Downloading `{filename}`...")
        with requests.get(cdn_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        st.success(f"✅ Downloaded `{filename}` successfully.")

        # Step 2: Detect MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        st.write(f"Detected MIME type: `{mime_type}`")

        # Step 3: Upload to Drime
        st.info("Uploading to Drime...")
        with open(filename, 'rb') as file_data:
            files = {'file': (filename, file_data, mime_type)}
            upload_res = requests.post("https://app.drime.cloud/api/v1/uploads", headers=headers, files=files)

        upload_data = upload_res.json()
        if upload_res.status_code != 200 or upload_data.get("status") != "success":
            st.error(f"❌ Upload failed: {upload_data}")
            os.remove(filename)
            st.stop()

        entry_id = upload_data["fileEntry"]["id"]
        st.success("✅ File uploaded to Drime.")

        # Step 4: Create shareable link
        st.info("Creating shareable link...")
        share_res = requests.post(
            f"https://app.drime.cloud/api/v1/file-entries/{entry_id}/shareable-link",
            headers=headers
        )

        if share_res.status_code == 200:
            share_url = share_res.json().get("url")
            st.success("✅ Shareable Link:")
            st.code(share_url)

            # Optional: Preview media
            if mime_type.startswith("video/"):
                st.video(share_url)
            elif mime_type.startswith("audio/"):
                st.audio(share_url)
            elif mime_type.startswith("image/"):
                st.image(share_url)

        else:
            st.error(f"❌ Failed to create shareable link: {share_res.text}")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
