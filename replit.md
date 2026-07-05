# Bot Grace

A Discord bot named Grace that replies to mentions using xAI's Grok model, with a Flask keep-alive web server.

## Stack
- **Language:** Python 3.12
- **Discord:** discord.py
- **AI:** xAI Grok via OpenAI-compatible API
- **Keep-alive:** Flask (port 8080)

## Running the bot
The workflow `Start application` runs `python Bot.py`.

It starts a Flask server in a background thread (port 8080), then connects the Discord bot.

## Required secrets
- `DISCORD_TOKEN` — Discord bot token
- `XAI_API_KEY` — xAI API key (from https://console.x.ai)

## Discord Developer Portal setup
The bot requires the **Message Content Intent** privileged gateway intent to be enabled at:
https://discord.com/developers/applications → your app → Bot → Privileged Gateway Intents

## How the bot works
- Responds when mentioned in a Discord channel
- Sends the user's message to Grok with Grace's personality system prompt
- Replies in Indonesian with a friendly, casual tone

## User preferences
