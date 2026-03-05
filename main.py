import streamlit as st
import requests
import base64
from io import BytesIO

API_URL = "https://ollamaapi.vercel.app/chat"

# ─── Page config ─────────────────────────────
st.set_page_config(page_title="AI Math Chat", page_icon="🤖", layout="wide")
st.title("🤖 AI Math Chat with Ollama VL")

# ─── Session state for messages ───────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ─── Sidebar: system prompt ───────────────────
system_prompt = st.sidebar.text_area(
    "System Prompt",
    value="You are a asstence."
)

# ─── Display chat ─────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        if isinstance(msg["content"], list):
            for part in msg["content"]:
                if part["type"] == "text":
                    st.markdown(f"**You:** {part['text']}")
                elif part["type"] == "image_url":
                    b64_data = part["image_url"]["url"].split(",")[1]
                    image_bytes = base64.b64decode(b64_data)
                    st.image(BytesIO(image_bytes), caption="Your Image", width=300)
        else:
            st.markdown(f"**You:** {msg['content']}")
    elif msg["role"] == "assistant":
        # Display math formulas nicely using LaTeX if present
        st.markdown(f"**AI:**")
        st.markdown(msg["content"], unsafe_allow_html=True)

# ─── User input ───────────────────────────────
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_area("Type your question here...", "")
    uploaded_files = st.file_uploader(
        "Attach image(s) (optional)", type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True
    )
    submitted = st.form_submit_button("Send")

if submitted and (user_input.strip() or uploaded_files):
    # ── Convert uploaded images to base64 ─────
    content_array = []
    if user_input.strip():
        content_array.append({"type": "text", "text": user_input})
    for file in uploaded_files:
        bytes_data = file.read()
        b64_str = base64.b64encode(bytes_data).decode("utf-8")
        content_array.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_str}"}})

    # Add user message to session
    st.session_state.messages.append({"role": "user", "content": content_array})

    # ── Prepare payload ───────────────
    payload = {
        "system": system_prompt,
        "messages": st.session_state.messages
    }

    # ── Stream AI response ───────────
    with st.spinner("AI is thinking..."):
        try:
            assistant_text = ""
            placeholder = st.empty()  # container to update AI message in real-time

            with requests.post(API_URL, json=payload, stream=True) as r:
                for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        assistant_text += chunk
                        # Live update
                        placeholder.markdown(f"**AI:** {assistant_text}", unsafe_allow_html=True)

            # Append AI response to session
            st.session_state.messages.append({"role": "assistant", "content": assistant_text})
        except Exception as e:
            st.error(f"Error: {e}")
