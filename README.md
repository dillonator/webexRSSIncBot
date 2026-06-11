# webexRSSIncBot

Parse specific Webex service RSS feeds and post **only incidents** to a Webex space — maintenance is filtered out, and each post shows the **latest status update**, not the whole history.

By default it watches these feeds (edit `FEEDS` in `webexIncBot.py` to customize):

- Commercial - Webex App — https://status.webex.com/Webex_App.rss
- Commercial - Webex Calling — https://status.webex.com/Webex_Calling.rss
- Commercial - Webex Contact Center — https://status.webex.com/Webex_Contact_Center.rss

Dependencies are managed with [uv](https://docs.astral.sh/uv/).

## How it works

- Polls each feed every `POLL_SECONDS` (default 120).
- Posts only when an incident is new or its status changes (dedup on incident ID + update timestamp).
- Skips scheduled maintenance windows.
- Records what it has posted in `seen.json` so it never double-posts across restarts.

## Prerequisites — create a Webex bot or use an existing bot if you already have a **bot token**

1. Create a bot at https://developer.webex.com/my-apps/new/bot and copy the **bot token** (shown only once).
2. Add the bot to the target space, then get the **room ID**:
   - https://developer.webex.com/messaging/docs/api/v1/rooms/list-rooms
   - Run it on that page using your bot token and copy the space's `id`.

## Configuration

`bot.env` holds **secrets only**:

| Variable | Description | Required |
|----------|-------------|----------|
| `WEBEX_BOT_TOKEN` | Webex bot API token | Yes |
| `WEBEX_ROOM_ID` | Target Webex room ID | Yes |

Runtime config (defaults work out of the box):

| Variable | Description | Default |
|----------|-------------|---------|
| `POLL_SECONDS` | Seconds between polls | `120` (set in `docker-compose.yml`) |
| `STATE_FILE` | Dedup state file path | `seen.json` (local) / `/data/seen.json` (Docker) |
| `DEBUG` | `1` = parse and print only, post nothing | unset |

## Local development (uv)

```bash
git clone <repository-url>
cd webexRSSIncBot
uv sync
cp bot.env.example bot.env      # edit, paste your token + room ID
```

Run it:

```bash
uv run --env-file bot.env python webexIncBot.py --once    # single pass
DEBUG=1 uv run --env-file bot.env python webexIncBot.py    # parse only, no posts
uv run --env-file bot.env python webexIncBot.py            # continuous loop
```

Local runs create `seen.json` in the project folder. The first run seeds it silently (posts nothing); subsequent runs post only new updates.

## Deployment (Docker)

```bash
git clone <repository-url> && cd webexRSSIncBot
cp bot.env.example bot.env      # paste real token + room ID
docker compose up -d --build
docker compose logs -f
```

State persists in the `bot-state` named volume, so restarts and rebuilds won't re-post. To inspect it:

```bash
docker exec webex-status-bot cat /data/seen.json
```

## Notes

- `bot.env` and `seen.json` are gitignored — never commit them. If a token is ever exposed, rotate it at https://developer.webex.com/my-apps.
- Inspired by Webex's RSS parser bot guide: https://developer.webex.com/blog/how-to-create-your-own-rss-feed-parser-bot-for-webex