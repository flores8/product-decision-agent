import logging
from tools.slack import SlackClient
from models.TylerAgent import TylerAgent
from models.conversation import Conversation
from models.message import Message
from database.conversation_store import ConversationStore

logger = logging.getLogger(__name__)

class SlackEventHandler:
    def __init__(self, slack_client: SlackClient, tyler_agent: TylerAgent, conversation_store: ConversationStore):
        self.slack_client = slack_client
        self.tyler_agent = tyler_agent
        self.conversation_store = conversation_store

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

            # Create or get conversation
            conversation_id = f"slack-{channel}-{thread_ts}"
            conversation = self.conversation_store.get(conversation_id)
            if not conversation:
                # Create a title from the first message or a default
                title = f"{text[:30]}..." if len(text) > 30 else text
                conversation = Conversation(
                    id=conversation_id,
                    title=title
                )
                self.conversation_store.save(conversation)

            # Create and add user message
            user_message = Message(
                role="user",
                content=text,
                attributes={"slack_user": user}
            )
            conversation.add_message(user_message)
            self.conversation_store.save(conversation)

            # Trigger Tyler processing
            self.tyler_agent.go(conversation_id)

            # Send initial acknowledgment
            # self.slack_client.client.chat_postMessage(
            #     channel=channel,
            #     thread_ts=thread_ts,
            #     text=f"<@{user}>, I'll respond shortly."
            # )

            # Get the updated conversation and send Tyler's response
            updated_conversation = self.conversation_store.get(conversation_id)
            if updated_conversation:
                # Get the last assistant message
                assistant_messages = [msg for msg in updated_conversation.messages if msg.role == "assistant"]
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