import streamlit as st
from models.Tyler import TylerModel
import weave


def initialize_chat_history():
    if "messages" not in st.session_state:
        st.session_state.messages = []

def initialize_tyler():
    if "tyler" not in st.session_state:
        st.session_state.tyler = TylerModel(
            model_name="gpt-4o",
            temperature=0.7
        )

def main():
    st.title("Chat with Tyler")
    
    # Initialize chat history and Tyler model
    initialize_chat_history()
    initialize_tyler()
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("What would you like to discuss?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Get Tyler's response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.tyler.predict(prompt)
                st.markdown(response)
                
        # Add assistant's response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 