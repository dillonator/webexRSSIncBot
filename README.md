# webexRSSIncBot
Parse specific WebEx Service RSS feeds and post only Incidents to a WebEx space

Currently watching the following feeds:
    
- "Commercial - Webex App":            "https://status.webex.com/Webex_App.rss",   
- "Commercial - Webex Calling":        "https://status.webex.com/Webex_Calling.rss",
- "Commercial - Webex Contact Center": "https://status.webex.com/Webex_Contact_Center.rss",


Using uv for dependency management

## Prereqs - Create a new WebEx Bot or use existing (need bot token)
1. Setup a bot at https://developer.webex.com/ or https://developer.webex.com/my-apps/new/bot
2. Collect bot token and grab room ID using info here:
   - Either create the room and add bot or add bot to existing room, then grab the room ID:
   - https://developer.webex.com/messaging/docs/api/v1/rooms/list-rooms
   - Use the bot token to get the rooms it's a member off. Run straight on the page above to grab it
   - Note this for the steps below

## Developer Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd webexrssinc
   ```

2. **Install dependencies:**
   Using `uv`:
   ```bash
   uv sync --all-groups
   ```

3. **Configure environment variables:**
   Copy the example environment file and fill in your credentials:
   ```bash
   cp bot.env.example bot.env
   ```
    Edit bot.env and provide:
        - 'WEBEX_BOT_TOKEN='[your_bot_token_here]
        - 'WEBEX_ROOM_ID='[your_room_id_here]
        - 'STATE_FILE='[/path/to/seen.json]

4. **Run the application:**
   ```bash
   bash run.sh
   ```

## Configuration

The application uses the following environment variables (defined in `bot.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `WEBEX_BOT_TOKEN` | Webex Bot API Token | Required |
| `WEBEX_ROOM_ID` | Webex Room ID | Required |

## Deployment

### Using Docker

The project includes a `Dockerfile` optimized for production.

1. To clone to your environment, build a new image, issue the command
    ```bash
   git clone <repo link above> && cd ./webexRSSIncBot
   cp bot.env.example bot.env      # edit & paste real token + room ID. Clean up after build for hygiene
   docker compose up -d --build
   docker compose logs -f
    ```
