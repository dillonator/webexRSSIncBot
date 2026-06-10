# webexRSSIncBot
Parse specific WebEx Service RSS feeds and post incidents to a WebEx space
Currently watching the following feeds:
    - "Commercial - Webex App":            "https://status.webex.com/Webex_App.rss",
    - "Commercial - Webex Calling":        "https://status.webex.com/Webex_Calling.rss",
    - "Commercial - Webex Contact Center": "https://status.webex.com/Webex_Contact_Center.rss",

uv for dependency managment

## Prereqs - Add WebEx bot setup notes
1. Setup a bot at https://developer.webex.com/
2. Collect bot token and grab room ID using info here:
    ### TODO

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
        - 'STATE_FILE='[/path/to/seen.json] -- may change with docker

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

The project includes a multi-stage `Dockerfile` optimized for production.

1. To build a new image, issue the command
    ```bash
    cd webex-inc-bot
    cp bot.env.example bot.env      # then paste your real token + room ID
    docker compose up -d --build
    docker compose logs -f          # watch it start and poll
```