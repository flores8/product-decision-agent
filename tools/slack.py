import os
import json
import slack_sdk
import weave
from typing import List, Dict, Optional
import litellm

SLACK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "slack-post_to_slack",
            "description": "Posts a message to Slack. Important: understand the correct channel to post to from the user's message. Always ask the user for a channel if they haven't specified one. Do not post to very public channels like #general, unless specifically asked to.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "The Slack channel to post to"
                    },
                    "blocks": {
                        "type": "array",
                        "description": "The blocks to post to Slack",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "text": {"type": "object"}
                            }
                        }
                    }
                },
                "required": ["channel", "blocks"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "slack-generate_slack_blocks",
            "description": "Generates Slack blocks from content. Always use this when posting to slack to format complex messages to improve readability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content to be formatted for Slack"
                    }
                },
                "required": ["content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "slack-send_ephemeral_message",
            "description": "Sends an ephemeral message (only visible to a specific user) in a channel",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "The channel to send the message to"
                    },
                    "user": {
                        "type": "string",
                        "description": "The user ID who should see the message"
                    },
                    "text": {
                        "type": "string",
                        "description": "The message text"
                    }
                },
                "required": ["channel", "user", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "slack-reply_in_thread",
            "description": "Replies to a message in a thread",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel": {
                        "type": "string",
                        "description": "The channel containing the parent message"
                    },
                    "thread_ts": {
                        "type": "string",
                        "description": "The timestamp of the parent message"
                    },
                    "text": {
                        "type": "string",
                        "description": "The reply text"
                    },
                    "broadcast": {
                        "type": "boolean",
                        "description": "Whether to also broadcast the reply to the channel"
                    }
                },
                "required": ["channel", "thread_ts", "text"]
            }
        }
    }
]

class SlackClient:
    def __init__(self):
        self.token = os.environ.get("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("SLACK_BOT_TOKEN environment variable is required")
        
        self.client = slack_sdk.WebClient(token=self.token)

@weave.op(name="slack-post_to_slack")
def post_to_slack(*, channel: str, blocks: List[Dict]) -> bool:
    """
    Post blocks to a specified Slack channel.

    Args:
        channel (str): The Slack channel to post to. The '#' symbol will be added if not present.
        blocks (List[Dict]): A list of block kit blocks to be posted to Slack.

    Returns:
        bool: True if the message was posted successfully, False otherwise.
    """
    try:
        # Add '#' to the channel name if it's not already present
        if not channel.startswith('#'):
            channel = f'#{channel}'

        client = SlackClient().client
        response = client.chat_postMessage(channel=channel, blocks=blocks)
        return response['ok']
    except Exception as e:
        print(f"Error posting to Slack: {str(e)}")
        return False

@weave.op(name="slack-generate_slack_blocks")
def generate_slack_blocks(*, content: str) -> List[Dict]:
    """
    Generate Slack blocks from the given content using a chat completion.

    Args:
        content (str): The content to be formatted for Slack.

    Returns:
        List[Dict]: A list of Slack blocks.
    """
    prompt = f"""
    Convert the following content into Slack blocks format:

    {content}

    Respond with only the JSON for the Slack blocks. Do not include any explanations or additional text.
    """

    try:
        response = litellm.completion(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        raw_content = response.choices[0].message.content.strip()

        # Attempt to parse the JSON
        try:
            generated_blocks = json.loads(raw_content)
        except json.JSONDecodeError as json_err:            
            # Attempt to clean the content and parse again
            cleaned_content = raw_content.strip('`').strip()
            if cleaned_content.startswith('json'):
                cleaned_content = cleaned_content[4:].strip()
            
            try:
                generated_blocks = json.loads(cleaned_content)
            except json.JSONDecodeError:
                # If it still fails, return a simple block with error message
                return [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Error: Unable to generate valid Slack blocks. Raw output:\n```\n{raw_content}\n```"
                    }
                }]

        # Validate the structure of the generated blocks
        if not isinstance(generated_blocks, list):
            generated_blocks = [generated_blocks]

        return generated_blocks

    except Exception as e:
        # Handle any other exceptions
        error_message = f"An error occurred while generating Slack blocks: {str(e)}"
        return [{
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": error_message
            }
        }] 

@weave.op(name="slack-send_ephemeral_message")
def send_ephemeral_message(*, channel: str, user: str, text: str) -> bool:
    """Send an ephemeral message that's only visible to a specific user."""
    try:
        client = SlackClient().client
        response = client.chat_postEphemeral(
            channel=channel,
            user=user,
            text=text
        )
        return response['ok']
    except Exception as e:
        print(f"Error sending ephemeral message: {str(e)}")
        return False

@weave.op(name="slack-reply_in_thread")
def reply_in_thread(*, channel: str, thread_ts: str, text: str, broadcast: Optional[bool] = False) -> bool:
    """Reply to a message in a thread."""
    try:
        client = SlackClient().client
        response = client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=text,
            reply_broadcast=broadcast
        )
        return response['ok']
    except Exception as e:
        print(f"Error replying in thread: {str(e)}")
        return False 