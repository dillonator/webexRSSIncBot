# webexRSSIncBot
Parse specific WebEx Service RSS feeds and post incidents to a WebEx space

uv for dependency managment

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
        WEBEX_BOT_TOKEN=[your_bot_token_here]
        WEBEX_ROOM_ID=[your_room_id_here]
        STATE_FILE=[/path/to/seen.json] -- may change with docker

4. **Run the application:**
   ```bash
   bash run.sh
   ```
