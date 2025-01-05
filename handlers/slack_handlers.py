import logging
from tools.slack import SlackClient
from models.TylerAgent import TylerAgent
from models.thread import Thread
from models.message import Message
from database.thread_store import ThreadStore

logger = logging.getLogger(__name__)

class SlackEventHandler:
    def __init__(self, slack_client: SlackClient, tyler_agent: TylerAgent, thread_store: ThreadStore):
        self.slack_client = slack_client
        self.tyler_agent = tyler_agent
        self.thread_store = thread_store

    def handle_mention(self, event_data: dict) -> None:
        """
        Handle app_mention events when the bot is mentioned.
        
        Args:
            event_data (dict): The event data from Slack containing the mention details
        """
        try:
            channel = event_data.get('channel')
            thread_ts = event_data.get('thread_ts', event_data.get('ts'))  # Use parent thread if exists
            user = event_data.get('user')
            text = event_data.get('text')

            # Create or get thread
            thread_id = f"slack-{channel}-{thread_ts}"
            thread = self.thread_store.get(thread_id)
            if not thread:
                # Create a title from the first message or a default
                title = f"{text[:30]}..." if len(text) > 30 else text
                thread = Thread(
                    id=thread_id,
                    title=title
                )
                self.thread_store.save(thread)

            # Create and add user message
            user_message = Message(
                role="user",
                content=text,
                attributes={"slack_user": user}
            )
            thread.add_message(user_message)
            self.thread_store.save(thread)

            # Trigger Tyler processing
            self.tyler_agent.go(thread_id)

            # Send initial acknowledgment
            # self.slack_client.client.chat_postMessage(
            #     channel=channel,
            #     thread_ts=thread_ts,
            #     text=f"<@{user}>, I'll respond shortly."
            # )

            # Get the updated thread and send Tyler's response
            updated_thread = self.thread_store.get(thread_id)
            if updated_thread:
                # Get the last assistant message
                assistant_messages = [msg for msg in updated_thread.messages if msg.role == "assistant"]
                if assistant_messages:
                    last_response = assistant_messages[-1].content
                    if last_response:
                        self.slack_client.client.chat_postMessage(
                            channel=channel,
                            thread_ts=thread_ts,
                            text=last_response
                        )

        except Exception as e:
            logger.error(f"Error handling mention: {str(e)}")
            # Send error message to Slack
            if channel and thread_ts:
                self.slack_client.client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=f"Sorry, I encountered an error: {str(e)}"
                ) 