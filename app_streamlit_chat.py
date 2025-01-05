import streamlit as st
from models.TylerAgent import TylerAgent
import weave
from models.thread import Thread, Message
from utils.helpers import get_all_tools
from database.thread_store import ThreadStore
from config import WEAVE_PROJECT

def initialize_weave():
    if "weave_initialized" not in st.session_state:
        st.session_state.weave = weave.init(WEAVE_PROJECT)
        st.session_state.weave_initialized = True

def initialize_chat():
    if "thread_id" not in st.session_state:
        reset_chat()

def initialize_tyler():
    if "tyler" not in st.session_state:
        tools = get_all_tools()
        st.session_state.tyler = TylerAgent(
            tools=tools,
            context="internal company documentation is in notion"
        )

def reset_chat():
    st.session_state.thread_id = None
    # Clear URL parameters and force rerun
    st.query_params.clear()

def log_feedback(weave_call, reaction):
    """
    Log feedback for a given call to Weave.

    Args:
    weave_call (dict): Dictionary containing weave call information (id and ui_url)
    reaction (str): The emoji representing the feedback (e.g., "👍" or "👎").
    """
    if not weave_call:
        raise ValueError("Cannot log feedback: call info is None")
        
    try:
        # Get the actual call object from Weave using the ID
        call = st.session_state.weave.get_call(weave_call["id"])
        # Add feedback directly to the call object
        call.feedback.add_reaction(reaction)
        print(f"Feedback logged: {reaction} for call {weave_call['id']}")
    except Exception as e:
        print(f"Error logging feedback: {str(e)}")
        # Include more context in the error
        raise Exception(f"Failed to log feedback ({reaction}) for call {weave_call['id']}: {str(e)}") from e

def display_message(message, is_user):
    """Display a chat message with feedback buttons for assistant messages"""
    content = f"Called: {message.name}" if message.role == 'function' else message.content

    # Set avatar to code icon for function messages
    avatar = ":material/code:" if message.role == 'function' else None
    message_container = st.chat_message("user" if is_user else "assistant", avatar=avatar)
    with message_container:
        st.markdown(content)
        
        # Add feedback and trace link for assistant messages only
        weave_call = message.attributes.get("weave_call")
        if not is_user and weave_call:
            # Generate a unique key for each feedback component
            feedback_key = f"feedback_{weave_call['id']}"
            
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
                            log_feedback(weave_call, reaction)
                            st.toast("Thanks for your feedback!", icon="✅")
                        except Exception as e:
                            st.error(f"Failed to log feedback: {str(e)}")
                
                with col2:
                    # Add some vertical spacing to align with feedback
                    st.markdown(
                        f'<a href="{weave_call["ui_url"]}" target="_blank" style="text-decoration: none;" class="weave-link">View trace in Weave</a>', 
                        unsafe_allow_html=True
                    )

def display_sidebar():
    # Create two columns in the sidebar for title and button
    col1, col2 = st.sidebar.columns([0.8, 0.2])
    
    # Put title in first column
    col1.title("Threads")
    
    # Put New Chat button in second column
    with col2:
        st.markdown('<div style="height: 100%; display: flex; align-items: center; justify-content: flex-end; padding-top: 0.5rem;">', unsafe_allow_html=True)
        if st.button("＋", key="new_chat", type="secondary", use_container_width=True):
            reset_chat()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    thread_store = ThreadStore()
    threads = thread_store.list_recent(limit=30)
    
    # Container for thread list
    with st.sidebar.container():
        for thread in threads:
            title = thread.title or "Untitled Chat"
            if st.button(
                title, 
                key=f"thread_{thread.id}", 
                type="tertiary", 
                use_container_width=True
            ):
                st.query_params["thread_id"] = thread.id
                st.session_state.thread_id = thread.id
                st.rerun()

def main():
    # Initialize weave once when the app starts
    initialize_weave()
    
    # Check for thread_id in URL parameters
    if "thread_id" in st.query_params:
        st.session_state.thread_id = st.query_params["thread_id"]
    
    # Display sidebar
    display_sidebar()
    
    # Create columns with custom CSS to vertically align contents
    st.markdown("""
        <style>
        .stButton {
            margin-top: 0px !important;
        }
        .weave-link {
            font-size: 0.8em;
            color: #666 !important;
        }
        /* Sidebar button styling */
        div[data-testid="stSidebarUserContent"] button[kind="tertiary"] {
            width: 100% !important;
            padding: 0px !important;
            margin: 0px !important;
            line-height: 1;
            border: none;
            background: none;
            display: flex !important;
            justify-content: flex-start !important;
            min-height: 0px !important;
        }
        div[data-testid="stSidebarUserContent"] button[kind="tertiary"] > div {
            width: 100% !important;
            text-align: left !important;
            display: flex !important;
            justify-content: flex-start !important;
            padding: 0px !important;
        }
        div[data-testid="stSidebarUserContent"] button[kind="tertiary"] p {
            text-align: left !important;
            margin: 0 !important;
            width: 100% !important;
            line-height: 1.5;
        }
        div[data-testid="stSidebarUserContent"] button[kind="tertiary"]:hover {
            color: rgb(255, 75, 75) !important;
            background: none !important;
        }
        /* Remove extra spacing in sidebar containers */
        div[data-testid="stSidebarUserContent"] .element-container {
            margin: 0px !important;
            padding: 0px !important;
        }
        div[data-testid="stSidebarUserContent"] .stButton {
            margin: 0px !important;
            padding: 0px !important;
            line-height: 1;
        }
        /* Style for the + button */
        button[data-testid="stBaseButton-secondary"] {
            background: transparent !important;
            color: inherit !important;
            border-radius: 0.5rem !important;
            padding: 0 0.75rem !important;
            cursor: pointer !important;
            font-size: 1rem !important;
            line-height: 1 !important;
            width: auto !important;
        }
        button[data-testid="stBaseButton-secondary"]:hover {
            color: inherit !important;
        }
        /* Remove default Streamlit button padding */
        .stButton {
            margin-top: 0px !important;
            padding: 0px !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize chat and Tyler model
    initialize_chat()
    initialize_tyler()
    
    # Get current thread
    thread_store = ThreadStore()
    thread = thread_store.get(st.session_state.thread_id)
    
    # Display chat messages if thread exists
    if thread:
        for message in thread.messages:
            if message.role != "system":  # Skip system messages in display
                display_message(message, message.role == "user")
    
    # Chat input
    if prompt := st.chat_input("What would you like to discuss?"):
        # Create thread if it doesn't exist
        if not thread:
            # Use first 20 chars of prompt as title, with first letter capitalized
            title = prompt[:30].capitalize() + "..." if len(prompt) > 20 else prompt.capitalize()
            thread = Thread(
                title=title
            )
            st.session_state.thread_id = thread.id
        
        # Add user message
        user_message = Message(
            role="user",
            content=prompt
        )
        thread.add_message(user_message)
        thread_store.save(thread)
        
        # Display user message immediately using display_message
        display_message(user_message, is_user=True)
            
        # Get assistant response
        with st.spinner("Thinking..."):
            try:
                with weave.attributes({'thread_id': thread.id}):
                    response, call = st.session_state.tyler.go.call(self=st.session_state.tyler, thread_id=thread.id)

                    # Get thread again to ensure we have latest state
                    thread = thread_store.get(thread.id)
                    
                    # Store only the essential serializable information from the weave call
                    thread.messages[-1].attributes["weave_call"] = {
                        "id": str(call.id),  # Ensure ID is a string
                        "ui_url": str(call.ui_url)  # Ensure URL is a string
                    }
                    thread_store.save(thread)
                
                # Force Streamlit to rerun, which will display the new messages in the history loop
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 