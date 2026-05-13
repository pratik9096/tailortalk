"""
TailorTalk - Streamlit Frontend
"""

# import streamlit as st
# import requests
# import json

# st.set_page_config(
#     page_title="TailorTalk",
#     page_icon="🔍",
#     layout="wide"
# )

# st.markdown("""
# <style>
#     .main { padding: 1rem; }
#     .file-item {
#         background: white;
#         border: 1px solid #ddd;
#         border-radius: 8px;
#         padding: 1rem;
#         margin: 0.5rem 0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Session state
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # API_URL = st.secrets.get("API_URL", "http://localhost:8000")
# # Sidebar
# API_URL = "http://localhost:8000"


import streamlit as st
import requests
import json

st.set_page_config(
    page_title="TailorTalk",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .main {
        padding: 1rem;
    }

    .file-item {
        background-color: #262730;
        color: white;
        border: 1px solid #444;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }

    .stChatMessage {
        padding: 10px;
    }

    a {
        color: #4da6ff !important;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# API URL
API_URL = "https://web-production-3e422.up.railway.app"

with st.sidebar:
    st.title("⚙️ Settings")
    api_input = st.text_input("API URL", value=API_URL)
    
    if st.button("Check Connection"):
        try:
            r = requests.get(f"{api_input}/health", timeout=5)
            if r.status_code == 200:
                st.success("✅ Connected")
                st.json(r.json())
            else:
                st.error("Error")
        except:
            st.error("Can't connect to API")
    
    st.divider()
    st.markdown("""
    ### How to Use
    - Type your search query
    - Examples:
      - "Find all PDFs"
      - "Show me recent spreadsheets"
      - "Find files about budget"
    """)
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main UI
st.title("🔍 TailorTalk")
st.markdown("Search your Google Drive with AI")

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        if "files" in msg and msg["files"]:
            st.divider()
            st.subheader("Files Found")
            for f in msg["files"]:
                st.markdown(f"""
                <div class="file-item">
                    <b>{f['name']}</b><br>
                    Type: {f.get('mimeType', '?')}<br>
                    <a href="{f.get('webViewLink', '#')}" target="_blank">Open →</a>
                </div>
                """, unsafe_allow_html=True)

# Input
user_input = st.chat_input("Search your Drive...")

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.spinner("Searching..."):
        try:
            payload = {
                "query": user_input,
                "conversation_history": [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                ]
            }
            
            response = requests.post(
                f"{api_input}/search",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data.get("response", ""),
                    "files": data.get("files", [])
                })
                
                with st.chat_message("assistant"):
                    st.markdown(data.get("response", ""))
                    
                    if data.get("files"):
                        st.divider()
                        st.subheader("Files Found")
                        for f in data.get("files", []):
                            st.markdown(f"""
                            <div class="file-item">
                                <b>{f['name']}</b><br>
                                Type: {f.get('mimeType', '?')}<br>
                                <a href="{f.get('webViewLink', '#')}" target="_blank">Open →</a>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.error(f"Error: {response.status_code}")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

st.divider()
st.markdown("TailorTalk v1.0")
