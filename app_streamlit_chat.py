import streamlit as st
from models.TylerAgent import TylerAgent
import weave
import uuid
from models.conversation import Conversation, Message
from utils.helpers import get_all_tools
from database.conversation_store import ConversationStore

def initialize_weave():
    if "weave_initialized" not in st.session_state:
        weave.init("company-of-agents/tyler")
        st.session_state.weave_initialized = True

def create_new_conversation() -> str:
    """Helper function to create a new conversation and return its ID"""
    conversation = Conversation(
        id=str(uuid.uuid4()),
        title="New Chat"
    )
    conversation_store = ConversationStore()
    conversation_store.save(conversation)
    return conversation.id

def initialize_chat():
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = create_new_conversation()

def initialize_tyler():
    if "tyler" not in st.session_state:
        tools = get_all_tools()
        st.session_state.tyler = TylerAgent(
            tools=tools,
            context="internal company documentation is in notion"
        )

def reset_chat():
    st.session_state.conversation_id = create_new_conversation()

def log_feedback(call, reaction):
    """
    Log feedback for a given call to Weave.

    Args:
    call (weave.Call): The Weave call object to log feedback for.
    reaction (str): The emoji representing the feedback (e.g., "👍" or "👎").
    """
    if not call:
        raise ValueError("Cannot log feedback: call object is None")
        
    try:
        # Add feedback directly to the call object
        call.feedback.add_reaction(reaction)
        print(f"Feedback logged: {reaction} for call {call.id}")
    except Exception as e:
        print(f"Error logging feedback: {str(e)}")
        # Include more context in the error
        raise Exception(f"Failed to log feedback ({reaction}) for call {call.id}: {str(e)}") from e

def display_message(message, is_user, call_obj=None):
    """Display a chat message with feedback buttons for assistant messages"""
    content = f"Called: {message.name}" if message.role == 'function' else message.content

    # Set avatar to code icon for function messages
    avatar = ":material/code:" if message.role == 'function' else None
    message_container = st.chat_message("user" if is_user else "assistant", avatar=avatar)
    with message_container:
        st.markdown(content)
        
        # Add feedback and trace link for assistant messages only
        if not is_user and call_obj:
            # Generate a unique key for each feedback component
            feedback_key = f"feedback_{call_obj.id}"
            
            # Create a container for feedback and trace link
            feedback_container = st.container()
            
            # Use columns to align feedback and trace link horizontally
            with feedback_container:
                col1, col2 = st.columns([.15, .85])
                with col1:
                    feedback = st.feedback(
                        options="thumbs",  # Use thumbs up/down options
                        key=feedback_key
                    )
                    
                    # Handle feedback when received
                    if feedback is not None:
                        try:
                            reaction = "👎" if feedback == 0 else "👍"
                            log_feedback(call_obj, reaction)
                            st.toast("Thanks for your feedback!", icon="✅")
                        except Exception as e:
                            st.error(f"Failed to log feedback: {str(e)}")
                
                with col2:
                    # Add some vertical spacing to align with feedback
                    st.markdown(
                        f'<a href="{call_obj.ui_url}" target="_blank" style="text-decoration: none;" class="weave-link">View trace in Weave</a>', 
                        unsafe_allow_html=True
                    )

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
    
    # Get current conversation
    conversation_store = ConversationStore()
    conversation = conversation_store.get(st.session_state.conversation_id)
    
    # Display chat messages
    for message in conversation.messages:
        if message.role != "system":  # Skip system messages in display
            call_obj = message.attributes.get("weave_call") if message.role == "assistant" else None
            display_message(message, message.role == "user", call_obj)
    
    # Chat input
    if prompt := st.chat_input("What would you like to discuss?"):
        # Add user message
        user_message = Message(
            role="user",
            content=prompt
        )
        conversation.add_message(user_message)
        conversation_store.save(conversation)
        
        # Display user message immediately using display_message
        display_message(user_message, is_user=True)
            
        # Get assistant response
        with st.spinner("Thinking..."):
            try:
                with weave.attributes({'conversation_id': conversation.id}):
                    response, call = st.session_state.tyler.go.call(self=st.session_state.tyler, conversation_id=conversation.id)
                    
                    # Update the attributes of the last message with the Weave call
                    conversation.messages[-1].attributes["weave_call"] = call
                
                # Force Streamlit to rerun, which will display the new messages in the history loop
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 