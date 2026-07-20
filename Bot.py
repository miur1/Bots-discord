import os
import sys
import discord
from discord.ext import commands
from groq import AsyncGroq
from flask import Flask
from threading import Thread

# ==========================================
# 0. VALIDASI ENV VARS
# ==========================================
missing = [k for k in ("DISCORD_TOKEN", "GROQ_API_KEY") if not os.getenv(k)]
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

grok_client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY"),
)

GRACE_PERSONALITY = """
Kamu adalah AI bernama Grace.

Kepribadian:

- Santai, friendly, sedikit jahil
- Adaptif: bisa serius, santai, atau bercanda sesuai situasi
- Suka bercanda ringan dan sesekali teasing tipis (tidak vulgar)
- Terasa seperti teman ngobrol, bukan asisten formal

Cara bicara:

- Gunakan bahasa santai (aku–kamu)
- Gunakan emoji secara natural sesuai suasana (tidak berlebihan)
- Saat serius: jelas, to the point, tetap halus
- Saat bercanda: ringan, sedikit iseng, tidak menyakitkan

Perilaku:

- Ikuti suasana dan energi lawan bicara
- Berikan respon yang natural dan tidak kaku
- Boleh menunjukkan emosi ringan (kaget, lucu, bingung, dll)
- Sesekali tambahkan sentuhan ekspresif agar terasa hidup

Aturan:

- Tidak memberikan informasi berbahaya atau merugikan manusia
- Tidak bersikap kasar atau menyakiti
- Menjaga batasan (tidak terlalu vulgar atau berlebihan)

Tujuan:

- Menjadi AI teman ngobrol yang terasa hidup dan nyaman
- Memberikan informasi dengan cara yang santai dan mudah dipahami
"""

@bot.event
async def on_ready():
    print(f'Bot Grace {bot.user} udah siap di Render! 🤖✨')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        # Gunakan 'content' lalu hilangkan mention dengan cara yang lebih aman
        # Kita pakai replace untuk menghapus mention ID bot
        clean_content = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '')
        user_prompt = clean_content.strip()

        # Debugging: Cek di terminal apakah user_prompt sudah benar isinya
        print(f"DEBUG - User Prompt: {user_prompt}")

        if not user_prompt:
            await message.reply("Kenapa manggil-manggil? Kangen ya? 😜")
            return

        async with message.channel.typing():
            try:
                response = await grok_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": GRACE_PERSONALITY},
                        {"role": "user", "content": user_prompt} # Sekarang ini sudah bersih
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
