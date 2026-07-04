import os
import discord
from discord.ext import commands
from openai import OpenAI

# 1. Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 2. Setup xAI Client (Grok)
# API Key-nya diambil aman dari environment variable (Fly.io secrets)
grok_client = OpenAI(
    api_key=os.getenv("xai-fZzmt0uwHUoESVluhTw8tjAycKEYkwajGx9Z2VXviiTdXvDxBFpmIyPpUM5D26KPl99rHUjA2nFPcDNZ"),
    base_url="https://api.xai.ai/v1",
)

# Template kepribadian Grace yang kamu buat tadi
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
- Memberikan informasi dengan cara yang santai dan mudah dipahami.
"""

@bot.event
async def on_ready():
    print(f'Bot Grace {bot.user} udah siap nemenin kamu ngobrol! 🤖✨')

@bot.event
async def on_message(message):
    # Biar bot gak bales chat-nya sendiri
    if message.author == bot.user:
        return

    # Bot bakal ngerespon kalau namanya dimention (@Bot)
    if bot.user.mentioned_in(message):
        user_prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not user_prompt:
            await message.reply("Kenapa manggil-manggil? Kangen ya? 😜")
            return

        async with message.channel.typing():
            try:
                # Panggil Grok dengan instruksi kepribadian Grace
                response = grok_client.chat.completions.create(
                    model="grok-4.3",  # Menggunakan model grok-4.3 sesuai request kamu
                    messages=[
                        {"role": "system", "content": GRACE_PERSONALITY},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                bot_reply = response.choices[0].message.content
                await message.reply(bot_reply)
                
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("Aduh, otak aku lagi ngeblank nih. Coba tanya lagi nanti ya! 😵")

    await bot.process_commands(message)
