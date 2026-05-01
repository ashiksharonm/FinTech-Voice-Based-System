import streamlit as st
import requests
import os
import base64
from audio_recorder_streamlit import audio_recorder

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Chat Interface", page_icon="💬")

st.title("💬 B2B Debt Discovery Chat")
st.markdown("Talk to our virtual assistant to find the right debt product for your enterprise.")

# Initialize session state for messages and session_id
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# Sidebar for Voice Input
with st.sidebar:
    st.markdown("### Voice Chat 🎤")
    st.markdown("Click the microphone to speak with the assistant.")
    audio_bytes = audio_recorder(text="Click to record", icon_name="microphone", icon_size="3x")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Check if new audio was recorded
if audio_bytes and audio_bytes != st.session_state.last_audio:
    st.session_state.last_audio = audio_bytes
    
    with st.spinner("Transcribing and thinking..."):
        # We need to send this to the backend
        files = {"audio_file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {}
        if st.session_state.session_id:
            data["session_id"] = st.session_state.session_id
            
        try:
            response = requests.post(f"{BACKEND_URL}/chat/voice", files=files, data=data)
            if response.status_code == 200:
                res_data = response.json()
                bot_response = res_data["response"]
                user_text = res_data.get("user_message", "🎤 (Voice Message)")
                audio_base64 = res_data.get("audio_base64")
                st.session_state.session_id = res_data["session_id"]
                
                # Display user's transcribed message
                st.chat_message("user").markdown(user_text)
                st.session_state.messages.append({"role": "user", "content": user_text})
                
                # Display bot response
                with st.chat_message("assistant"):
                    st.markdown(bot_response)
                    if audio_base64:
                        audio_data = base64.b64decode(audio_base64)
                        st.audio(audio_data, format="audio/mp3", autoplay=True)
                        
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
            else:
                st.error(f"Error from API: {response.text}")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")

# React to user text input
elif prompt := st.chat_input("What is your company's revenue?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Call Backend API
    with st.spinner("Thinking..."):
        payload = {"message": prompt}
        if st.session_state.session_id:
            payload["session_id"] = st.session_state.session_id
            
        try:
            response = requests.post(f"{BACKEND_URL}/chat", json=payload)
            if response.status_code == 200:
                data = response.json()
                bot_response = data["response"]
                st.session_state.session_id = data["session_id"]
                
                # Display bot response
                with st.chat_message("assistant"):
                    st.markdown(bot_response)
                # Add bot response to chat history
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
            else:
                st.error(f"Error from API: {response.status_code}")
        except Exception as e:
            st.error(f"Failed to connect to backend: {e}")
