import streamlit as st
from models.TylerModel import TylerModel
import weave
import uuid

def initialize_weave():
    if "weave_initialized" not in st.session_state:
        weave.init("company-of-agents/tyler")
        st.session_state.weave_initialized = True

def initialize_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

def initialize_tyler():
    if "tyler" not in st.session_state:
        st.session_state.tyler = TylerModel()

def reset_chat():
    st.session_state.messages = []
    st.session_state.thread_id = str(uuid.uuid4())

def main():
    # Initialize weave once when the app starts
    initialize_weave()
    
    # Rest of the main function remains unchanged
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title("Chat with Tyler")
    
    with col2:
        if st.button("New Thread", type="primary"):
            reset_chat()
            st.rerun()
    
    # Initialize chat history and Tyler model
    initialize_chat_history()
    initialize_tyler()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "call" in message:
                st.markdown(f'<a href="{message["call"].ui_url}" target="_blank" style="text-decoration: none; color: inherit;">Weave</a>', unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("What would you like to discuss?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with weave.attributes({'thread_id': st.session_state.thread_id}):
                response, call = st.session_state.tyler.predict.call(self=st.session_state.tyler, messages=st.session_state.messages)
            st.markdown(response)
            st.markdown(f'<a href="{call.ui_url}" target="_blank" style="text-decoration: none; color: inherit;">View trace in Weave</a>', unsafe_allow_html=True)
                
        st.session_state.messages.append({"role": "assistant", "content": response, "call": call})

if __name__ == "__main__":
    main() 