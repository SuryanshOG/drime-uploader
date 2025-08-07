import streamlit as st
import requests
import os
import mimetypes
import re

st.set_page_config(page_title="Drime CDN Uploader", layout="centered")
st.title("🚀 Upload File to Drime from a CDN URL")

# 🔐 Drime API Token
API_TOKEN = st.secrets.get("DRIME_API_TOKEN", os.getenv("DRIME_API_TOKEN"))
if not API_TOKEN:
    st.error("❌ Missing Drime API token. Set it in Streamlit secrets or as an environment variable.")
    st.stop()

# 🌐 Input from user
cdn_url = st.text_input("Paste the direct CDN/download URL of the file")

if st.button("Upload to Drime") and cdn_url:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": cdn_url
    }

    try:
        # Step 1: Make HEAD request to get filename
        filename = None
        head = requests.head(cdn_url, headers=headers, allow_redirects=True)
        cd = head.headers.get("Content-Disposition")
        if cd:
            match = re.findall("filename=\"?([^\";]+)\"?", cd)
            if match:
                filename = match[0]

        if not filename:
            filename = cdn_url.split("/")[-1].split("?")[0] or "downloaded_file"

        st.info(f"📥 Downloading `{filename}`...")
        r = requests.get(cdn_url, stream=True, headers=headers, timeout=60)
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        chunk_size = 8192
        downloaded = 0
        progress_bar = st.progress(0, text="Downloading...")

        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = int(downloaded * 100 / total_size)
                    progress_bar.progress(percent, text=f"Downloading... {percent}%")

        progress_bar.empty()
        st.success(f"✅ Downloaded `{filename}` successfully.")

        # Step 2: Detect MIME
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        st.write(f"📄 Detected MIME type: `{mime_type}`")

        # Step 3: Upload to Drime
        st.info("📤 Uploading to Drime...")
        with open(filename, 'rb') as file_data:
            files = {'file': (filename, file_data, mime_type)}
            upload_res = requests.post(
                "https://app.drime.cloud/api/v1/uploads",
                headers={"Authorization": f"Bearer {API_TOKEN}"},
                files=files
            )

        upload_data = upload_res.json()
        if upload_res.status_code != 200 or upload_data.get("status") != "success":
            st.error(f"❌ Upload failed: {upload_data}")
            os.remove(filename)
            st.stop()

        entry_id = upload_data["fileEntry"]["id"]
        st.success("✅ File uploaded to Drime.")

        # Step 4: Create shareable link
        st.info("🔗 Creating shareable link...")
        share_res = requests.post(
            f"https://app.drime.cloud/api/v1/file-entries/{entry_id}/shareable-link",
            headers={"Authorization": f"Bearer {API_TOKEN}"}
        )

        if share_res.status_code == 200:
            share_url = share_res.json().get("url")
            st.success("✅ Shareable Link:")
            st.code(share_url)

            # Preview
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
