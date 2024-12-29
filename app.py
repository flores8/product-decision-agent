import streamlit as st
from models.Tyler import TylerModel
import weave

def initialize_weave():
    if "weave_initialized" not in st.session_state:
        weave.init("company-of-agents/tyler")
        st.session_state.weave_initialized = True

def initialize_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []

def initialize_tyler():
    if "tyler" not in st.session_state:
        st.session_state.tyler = TylerModel()

def reset_chat():
    st.session_state.messages = []

def main():
    # Initialize weave once when the app starts
    initialize_weave()
    
    # Rest of the main function remains unchanged
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title("Chat with Tyler")
    
    with col2:
        if st.button("New Chat", type="primary"):
            reset_chat()
            st.rerun()
    
    # Initialize chat history and Tyler model
    initialize_chat_history()
    initialize_tyler()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to discuss?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            response = st.session_state.tyler.predict(prompt)
            st.markdown(response)
                
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 