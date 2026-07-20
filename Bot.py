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
    return "Bot Miu si femboy imut sudah online dan siap ngobrol! 🚀"

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

user_memories = {}
MAX_MEMORY = 5

GRACE_PERSONALITY = """
Kamu adalah AI bernama Miu si femboy imut.

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

# ==========================================
# Variabel untuk menyimpan ingatan Grace
# ==========================================
user_memories = {}
MAX_MEMORY = 5 # Jumlah pasang percakapan yang diingat (5 tanya + 5 jawab)

@bot.event
async def on_ready():
    print(f'Bot Miu si femboy imut {bot.user} udah siap di Render! 🤖✨')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        # 1. Bersihkan pesan dari mention
        clean_content = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()

        if not clean_content:
            await message.reply("Kenapa manggil-manggil? Kangen ya? 😜")
            return

        # 2. Setup memori untuk user yang nge-chat
        user_id = message.author.id
        if user_id not in user_memories:
            user_memories[user_id] = [] # Buat list kosong kalau user baru pertama kali chat

        # 3. Tambahkan pesan user ke dalam memori
        user_memories[user_id].append({"role": "user", "content": clean_content})

        # 4. Batasi panjang memori (dikali 2 karena 1 pasang = 1 user + 1 assistant)
        if len(user_memories[user_id]) > (MAX_MEMORY * 2):
            # Ambil yang paling baru saja, buang yang paling lama
            user_memories[user_id] = user_memories[user_id][-(MAX_MEMORY * 2):]

        # 5. Siapkan prompt yang akan dikirim ke API (System + History)
        api_messages = [{"role": "system", "content": GRACE_PERSONALITY}]
        api_messages.extend(user_memories[user_id])

        async with message.channel.typing():
            try:
                # 6. Kirim seluruh ingatan ke Groq
                response = await grok_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=api_messages
                )
                bot_reply = response.choices[0].message.content
                
                # 7. Simpan jawaban Grace ke dalam memori supaya dia ingat apa yang dia ucapkan
                user_memories[user_id].append({"role": "assistant", "content": bot_reply})
                
                await message.reply(bot_reply)
            except Exception as e:
                print(f"Error: {e}")
                # Hapus pesan terakhir user dari memori jika terjadi error (biar gak nyangkut)
                if len(user_memories[user_id]) > 0:
                    user_memories[user_id].pop()
                    
                await message.reply("Aduh, otak aku lagi ngeblank nih. Coba lagi ya! 😵")

    await bot.process_commands(message)

# ==========================================
# 3. JALANKAN WEB SERVER & BOT
# ==========================================
if __name__ == "__main__":
    keep_alive()  # Jalankan web server di background
    bot.run(os.getenv('DISCORD_TOKEN'))
