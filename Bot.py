import os
import sys
import discord
from discord.ext import commands
from openai import AsyncOpenAI
from flask import Flask
from threading import Thread

# ==========================================
# 0. VALIDASI ENV VARS
# ==========================================
missing = [k for k in ("DISCORD_TOKEN", "XAI_API_KEY") if not os.getenv(k)]
if missing:
    sys.exit(f"[ERROR] Environment variable(s) belum diset: {', '.join(missing)}")

# ==========================================
# 1. SETUP WEB SERVER MINI (Biars Gak Sleep)
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Bot Grace sudah online dan siap ngobrol! 🚀"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web_server)
    t.start()

# ==========================================
# 2. SETUP DISCORD BOT & GROK
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

grok_client = AsyncOpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",
)

GRACE_PERSONALITY = """
Kamu adalah AI bernama Grace.
Kepribadian: Santai, friendly, sedikit jahil, adaptif, suka bercanda ringan.
Cara bicara: Gunakan bahasa santai (aku-kamu), emoji natural.
Aturan: Tidak membahayakan, menjaga batasan.
"""

@bot.event
async def on_ready():
    print(f'Bot Grace {bot.user} udah siap di Render! 🤖✨')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        # Handle both <@id> and <@!id> mention formats
        user_prompt = message.content
        for mention_fmt in (f'<@{bot.user.id}>', f'<@!{bot.user.id}>'):
            user_prompt = user_prompt.replace(mention_fmt, '')
        user_prompt = user_prompt.strip()

        if not user_prompt:
            await message.reply("Kenapa manggil-manggil? Kangen ya? 😜")
            return

        async with message.channel.typing():
            try:
                response = await grok_client.chat.completions.create(
                    model="grok-4.5",
                    messages=[
                        {"role": "system", "content": GRACE_PERSONALITY},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                bot_reply = response.choices[0].message.content
                await message.reply(bot_reply)
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("Aduh, otak aku lagi ngeblank nih. Coba lagi ya! 😵")

    await bot.process_commands(message)

# ==========================================
# 3. JALANKAN WEB SERVER & BOT
# ==========================================
if __name__ == "__main__":
    keep_alive()  # Jalankan web server di background
    bot.run(os.getenv('DISCORD_TOKEN'))
