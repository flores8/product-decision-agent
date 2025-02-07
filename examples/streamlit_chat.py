import streamlit as st
from dotenv import load_dotenv
import os
import asyncio
from functools import partial

# Load environment variables from .env file
load_dotenv()

from tyler.models.agent import Agent
import weave
from tyler.models.thread import Thread
from tyler.models.message import Message
from tyler.models.attachment import Attachment
from tyler.database.thread_store import ThreadStore
from tyler.database.config import get_database_url

def get_secret(key):
    """Get secret from environment variables"""
    return os.getenv(key)

def initialize_weave():
    if "weave_initialized" not in st.session_state:
        st.session_state.weave = weave.init("tyler")
        st.session_state.weave_initialized = True

def initialize_chat():
    if "thread_id" not in st.session_state:
        reset_chat()
    if "upload_counter" not in st.session_state:
        st.session_state.upload_counter = 0

async def initialize_tyler():
    if "tyler" not in st.session_state:
        # Initialize thread store with proper database configuration
        database_url = get_database_url()
        thread_store = ThreadStore(database_url)  # Pass database URL
        st.session_state.tyler = Agent(
            tools=["web", "command_line"],
            purpose="To help users with their questions and requests",
            notes="""- Our company policies are found in Notion
- Updates to company policies are frequently announced in Notion
- When searching for information in Notion, generalize your search query to find the most relevant information and compare several pages to ensure you have the most accurate information.
""",
            thread_store=thread_store  # Pass thread store to Agent
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
    # Skip assistant messages with tool_calls
    if message.role == "assistant" and getattr(message, "tool_calls", None):
        return
        
    # Set avatar to code icon for tool messages
    avatar = ":material/code:" if message.role == 'tool' else None
    message_container = st.chat_message("user" if is_user else "assistant", avatar=avatar)
    
    with message_container:
        # Track if we've displayed an image
        has_displayed_image = False
        has_text_content = False
        
        # Handle content based on type
        if isinstance(message.content, list):
            for content_item in message.content:
                if isinstance(content_item, dict):
                    if content_item.get("type") == "text":
                        st.markdown(content_item.get("text", ""))
                        has_text_content = True
                    elif content_item.get("type") == "image_url":
                        # Display base64 encoded image
                        image_url = content_item.get("image_url", {}).get("url", "")
                        if image_url.startswith("data:image"):
                            import base64
                            # Extract the base64 content after the comma
                            base64_data = image_url.split(",")[1]
                            image_bytes = base64.b64decode(base64_data)
                            st.image(image_bytes)
                        else:
                            st.image(image_url)
                        has_displayed_image = True
        else:
            # Display regular text content
            content = f"Called: {message.name}" if message.role == 'tool' else message.content
            st.markdown(content)
            if content.strip():
                has_text_content = True
        
        # Display attachments if any
        if message.attachments:
            non_image_attachments = [att for att in message.attachments 
                                   if not (att.mime_type and att.mime_type.startswith('image/'))]
            image_attachments = [att for att in message.attachments 
                               if att.mime_type and att.mime_type.startswith('image/')]
            
            # Determine if we should show the attachments section
            should_show_attachments = non_image_attachments or (image_attachments and not has_displayed_image and has_text_content)
            
            if should_show_attachments:
                st.markdown("**Attachments:**")
                
                # Show image attachment only if we haven't displayed one yet
                if image_attachments and not has_displayed_image:
                    attachment = image_attachments[0]  # Show only the first image
                    try:
                        # Only show filename if there's other content
                        if has_text_content or non_image_attachments:
                            st.markdown(f"*{attachment.filename}*")
                        
                        # Display the image
                        import base64
                        if isinstance(attachment.content, str):
                            # Handle base64 string
                            if attachment.content.startswith("data:image"):
                                # Extract the base64 content after the comma
                                base64_data = attachment.content.split(",")[1]
                                image_bytes = base64.b64decode(base64_data)
                            else:
                                image_bytes = base64.b64decode(attachment.content)
                        else:
                            # Handle bytes directly
                            image_bytes = attachment.content
                        st.image(image_bytes)
                    except Exception as e:
                        st.error(f"Error displaying image: {str(e)}")
                
                # Show non-image attachments
                for attachment in non_image_attachments:
                    if attachment.processed_content and "overview" in attachment.processed_content:
                        st.markdown(f"*{attachment.filename}* - {attachment.processed_content['overview']}")
                    else:
                        st.markdown(f"*{attachment.filename}*")
        
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

async def display_sidebar():
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
    
    # Initialize thread store with proper database configuration
    database_url = get_database_url()
    thread_store = ThreadStore(database_url)
    threads = await thread_store.list_recent(limit=30)
    
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

async def main():
    # Initialize weave once when the app starts
    initialize_weave()
    
    # Check for thread_id in URL parameters
    if "thread_id" in st.query_params:
        st.session_state.thread_id = st.query_params["thread_id"]
    
    # Initialize chat and Tyler model
    initialize_chat()
    await initialize_tyler()
    
    # Display sidebar
    await display_sidebar()
    
    # Initialize uploaded_files in session state if not present
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    
    # Get current thread
    database_url = get_database_url()
    thread_store = ThreadStore(database_url)
    thread = await thread_store.get(st.session_state.thread_id) if st.session_state.thread_id else None

    # Display chat messages first
    if thread:
        for message in thread.messages:
            if message.role != "system":  # Skip system messages in display
                display_message(message, message.role == "user")
    
    # Display file uploader only if there's no thread or last message is not from user
    should_show_uploader = True
    if thread and thread.messages:
        last_message = next((m for m in reversed(thread.messages) if m.role != "system"), None)
        if last_message and last_message.role == "user":
            should_show_uploader = False
    
    if should_show_uploader:
        # Display file uploader in a chat message after all messages
        with st.chat_message("assistant", avatar="📎"):
            uploaded_files = st.file_uploader(
                "Attach files",
                accept_multiple_files=True,
                key=f"file_uploader_{st.session_state.upload_counter}",
                label_visibility="collapsed"
            )
            if uploaded_files:
                st.session_state.uploaded_files = uploaded_files
                st.caption(f"*{len(uploaded_files)} files*")
    
    # Chat input at the bottom
    prompt = st.chat_input("What would you like to discuss?")
    
    if prompt:
        # Create thread if it doesn't exist
        if not thread:
            # Use first 20 chars of prompt as title, with first letter capitalized
            title = prompt[:30].capitalize() + "..." if len(prompt) > 20 else prompt.capitalize()
            thread = Thread(
                title=title
            )
            st.session_state.thread_id = thread.id
        
        # Get uploaded files
        uploaded_files = st.session_state.get('uploaded_files', [])
        
        # Add user message with any attachments
        user_message = Message(
            role="user",
            content=prompt
        )
        
        # Add any uploaded files as attachments
        for file in uploaded_files:
            user_message.attachments.append(Attachment(
                filename=file.name,
                content=file.getvalue()
            ))
        
        thread.add_message(user_message)
        await thread_store.save(thread)
        
        # Display user message immediately using display_message
        display_message(user_message, is_user=True)
            
        # Get assistant response
        with st.spinner("Thinking..."):
            try:
                with weave.attributes({'thread_id': thread.id}):
                    # Use asyncio.run to properly handle the async call
                    response, call = await st.session_state.tyler.go(thread.id)

                    # Get thread again to ensure we have latest state
                    thread = await thread_store.get(thread.id)
                    
                    # Store only the essential serializable information from the weave call
                    thread.messages[-1].attributes["weave_call"] = {
                        "id": str(call.id),  # Ensure ID is a string
                        "ui_url": str(call.ui_url)  # Ensure URL is a string
                    }
                    await thread_store.save(thread)
                
                # Clear uploaded files and increment counter to force file uploader refresh
                st.session_state.uploaded_files = []
                st.session_state.upload_counter += 1
                
                # Force Streamlit to rerun, which will display the new messages in the history loop
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

    # Create columns with custom CSS to vertically align contents
    st.markdown("""
        <style>
        /* Base styles */
        .stButton {
            margin-top: 0px !important;
        }
        .weave-link {
            font-size: 0.8em;
            color: #666 !important;
        }
        
        /* Sidebar styling */
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
        
        /* New Chat button styling */
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
        
        /* File uploader styling */
        .stFileUploader {
            padding-bottom: 0px !important;
        }
        .stFileUploader > div {
            padding: 0px !important;
        }
        
        /* Style the caption */
        .stCaption {
            margin-top: 0px !important;
            padding-top: 0px !important;
            text-align: center !important;
        }
        </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    asyncio.run(main()) 