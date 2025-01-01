import streamlit as st
from models.TylerModel import TylerModel
import weave
import uuid
from models.conversation import Conversation, Message

def initialize_weave():
    if "weave_initialized" not in st.session_state:
        weave.init("company-of-agents/tyler")
        st.session_state.weave_initialized = True

def create_new_conversation() -> Conversation:
    """Helper function to create a new conversation"""
    return Conversation(
        id=str(uuid.uuid4()),
        title="New Chat"
    )

def initialize_chat():
    if "conversation" not in st.session_state:
        st.session_state.conversation = create_new_conversation()

def initialize_tyler():
    if "tyler" not in st.session_state:
        st.session_state.tyler = TylerModel()

def reset_chat():
    st.session_state.conversation = create_new_conversation()

def main():
    # Initialize weave once when the app starts
    initialize_weave()
    
    # Create columns with custom CSS to vertically align contents
    st.markdown("""
        <style>
        .stButton {
            margin-top: 12px;
        }
        .weave-link {
            font-size: 0.8em;
            color: #666 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title("Chat with Tyler")
    
    with col2:
        container = st.container()
        container.empty()
        with container:
            st.write("")  # Single spacing should be enough
            st.button("New Chat", type="primary", on_click=reset_chat, use_container_width=True)
    
    # Initialize chat and Tyler model
    initialize_chat()
    initialize_tyler()
    
    # Display chat messages
    for message in st.session_state.conversation.messages:
        if message.role != "system":  # Skip system messages in display
            with st.chat_message(message.role):
                st.markdown(message.content)
                if message.role == "assistant" and "weave_call" in message.metadata:
                    st.markdown(
                        f'<a href="{message.metadata["weave_call"].ui_url}" target="_blank" style="text-decoration: none;" class="weave-link">View trace in Weave</a>', 
                        unsafe_allow_html=True
                    )
    
    # Chat input
    if prompt := st.chat_input("What would you like to discuss?"):
        # Add user message
        user_message = Message(
            role="user",
            content=prompt
        )
        st.session_state.conversation.add_message(user_message)
        
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Create a chat message container for the assistant
        with st.chat_message("assistant"):
            # Add a spinner while we wait for the response
            with st.spinner("Thinking..."):
                with weave.attributes({'conversation_id': st.session_state.conversation.id}):
                    response, call = st.session_state.tyler.predict.call(
                        self=st.session_state.tyler, 
                        messages=st.session_state.conversation.get_messages_for_chat_completion()
                    )
                st.markdown(response)
                st.markdown(
                    f'<a href="{call.ui_url}" target="_blank" style="text-decoration: none;" class="weave-link">View trace in Weave</a>', 
                    unsafe_allow_html=True
                )
                
        # Add assistant message
        assistant_message = Message(
            role="assistant",
            content=response,
            metadata={"weave_call": call}
        )
        st.session_state.conversation.add_message(assistant_message)

if __name__ == "__main__":
    main() 