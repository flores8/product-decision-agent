# Slack integration

The Slack module provides tools for interacting with Slack workspaces, allowing you to send messages, create channels, and manage users.

## Configuration

Before using Slack tools, you need to set up the following environment variables:

```bash
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-secret
```

You can get these credentials by:
1. Creating a Slack App in your workspace
2. Adding necessary bot scopes
3. Installing the app to your workspace

Required bot token scopes:
- `chat:write`
- `channels:manage`
- `groups:write`
- `im:write`
- `mpim:write`
- `users:read`
- `channels:read`

## Available tools

### Slack-post to slack

Posts a message to a Slack channel. The tool is careful about channel selection and requires explicit channel specification.

#### Parameters

- `channel` (string, required)
  - The Slack channel to post to
  - Can be:
    - Public channel name (e.g., "general")
    - Private channel name
    - Channel ID
  - Note: Be cautious with public channels

- `blocks` (array, required)
  - The blocks to post to Slack
  - Each block is an object with:
    - `type` (string): Block type (e.g., "section", "header")
    - `text` (object): Text content
  - Supports full [Slack Block Kit](https://api.slack.com/block-kit) format

#### Example Usage

```python
message = {
    "channel": "team-updates",
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Project Update"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "The project is *on track* and progressing well!"
            }
        }
    ]
}

# Agent will use this configuration to post to Slack
```

### Slack-create channel

Creates a new Slack channel.

#### Parameters

- `name` (string, required)
  - The name of the channel to create
  - Will be automatically converted to lowercase and hyphens
  - Must be unique in the workspace
  - Maximum 80 characters
  - Can only contain letters, numbers, hyphens, and underscores

- `is_private` (boolean, optional)
  - Whether to create a private channel
  - Default: false
  - Private channels can't be made public later

#### Example Usage

```python
# Create a public channel
create_public = {
    "name": "project-updates",
    "is_private": False
}

# Create a private channel
create_private = {
    "name": "team-confidential",
    "is_private": True
}
```

### Slack-invite to channel

Invites a user to a Slack channel.

#### Parameters

- `channel` (string, required)
  - The channel ID or name to invite the user to
  - Can be public or private channel
  - Bot must be a member of private channels

- `user` (string, required)
  - The user ID to invite to the channel
  - Must be a valid Slack user ID
  - Bot must have permission to invite users

#### Example Usage

```python
invite = {
    "channel": "project-updates",
    "user": "U0123456789"
}
```

## Best practices

1. **Channel Selection**
   - Be cautious with public channels
   - Always verify channel names
   - Use private channels for sensitive information

2. **Message Formatting**
   - Use Block Kit for rich formatting
   - Keep messages concise and clear
   - Use appropriate message types

3. **Error Handling**
   - Handle channel not found errors
   - Check user permissions
   - Validate channel names

4. **Rate Limiting**
   - Be aware of Slack API limits
   - Implement appropriate delays
   - Handle rate limit errors

## Common use cases

1. **Team Communication**
   - Project updates
   - Automated notifications
   - Status reports

2. **Channel Management**
   - Create project channels
   - Manage team spaces
   - Organize conversations

3. **User Management**
   - Invite team members
   - Manage channel access
   - Coordinate teams

## Security considerations

1. **Channel Access**
   - Verify channel visibility requirements
   - Use private channels for sensitive data
   - Regularly audit channel access

2. **Message Content**
   - Don't post sensitive information
   - Validate message content
   - Consider message retention policies

3. **API Tokens**
   - Secure storage of tokens
   - Regular token rotation
   - Monitor token usage 