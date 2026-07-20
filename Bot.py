import os
import random
import sys
import re
import asyncio
import aiohttp
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
# 1. SETUP WEB SERVER MINI (Biar Gak Sleep)
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
# 2. SETUP DISCORD BOT & GROQ
# ==========================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='Miu ', intents=intents)

grok_client = AsyncGroq(
    api_key=os.getenv("GROQ_API_KEY"),
)

user_memories = {}
MAX_MEMORY = 5  # Jumlah pasang percakapan yang diingat (5 tanya + 5 jawab)
alarm_tasks = {}

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
# ALARM
# ==========================================
async def jalankan_alarm(channel, user, durasi_detik, angka_waktu, satuan_waktu):
    try:
        await channel.send(f"Sip! Miu set timer buat {user.mention} selama {angka_waktu} {satuan_waktu}. Siap-siap aku teror nanti! 🕒😈")
        await asyncio.sleep(durasi_detik)

        while True:
            for _ in range(5):
                await channel.send(f"🔔 {user.mention} WOY! WAKTUNYA HABIS! BANGUUUN!")
                await asyncio.sleep(1.5)
            await asyncio.sleep(60)

    except asyncio.CancelledError:
        pass

# ==========================================
# KEEP-ALIVE PING (setiap 15 menit)
# ==========================================
async def keep_alive_ping():
    await bot.wait_until_ready()
    port = int(os.environ.get("PORT", 8080))
    url = f"http://127.0.0.1:{port}/"
    while not bot.is_closed():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    print(f"[Keep-Alive] Ping sukses — status {resp.status}")
        except Exception as e:
            print(f"[Keep-Alive] Ping gagal: {e}")
        await asyncio.sleep(15 * 60)

# ==========================================
# EVENTS
# ==========================================
@bot.event
async def on_ready():
    print(f'Bot Miu si femboy imut {bot.user} udah siap! 🤖✨')
    bot.loop.create_task(keep_alive_ping())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    isi_pesan = message.content.lower()

    # ==========================================
    # LOGIKA 1: Mematikan atau Membatalkan Alarm
    # ==========================================
    if "iya miu" in isi_pesan or "ga jadi miu" in isi_pesan:
        if message.author.id in alarm_tasks:
            alarm_tasks[message.author.id].cancel()
            del alarm_tasks[message.author.id]

            if "iya miu" in isi_pesan:
                await message.reply("Nah, gitu dong nyahut! 😌 Alarm udah Miu matiin ya.")
            else:
                await message.reply("Yee labil! Yaudah timer-nya Miu batalin. 🙄")
            return

    # ==========================================
    # LOGIKA 2: Bikin Timer Baru
    # ==========================================
    timer_match = re.search(r'miu buat timer (\d+)\s*(detik|menit|jam)', isi_pesan)
    if timer_match:
        angka = int(timer_match.group(1))
        satuan = timer_match.group(2)

        if satuan == 'detik':
            durasi = angka
        elif satuan == 'menit':
            durasi = angka * 60
        elif satuan == 'jam':
            durasi = angka * 3600

        if message.author.id in alarm_tasks:
            await message.reply("Eh tunggu dulu! Kamu kan masih punya timer yang lagi jalan. Matiin dulu yang lama (ketik `ga jadi Miu`), baru deh bikin yang baru! 🙄")
            return

        task = asyncio.create_task(jalankan_alarm(message.channel, message.author, durasi, angka, satuan))
        alarm_tasks[message.author.id] = task
        return

    # ==========================================
    # LOGIKA 3: Chat AI (kalau di-mention)
    # ==========================================
    if bot.user.mentioned_in(message):
        clean_content = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()

        if not clean_content:
            await message.reply("Kenapa manggil-manggil? Kangen ya? 😜")
            return

        user_id = message.author.id
        if user_id not in user_memories:
            user_memories[user_id] = []

        user_memories[user_id].append({"role": "user", "content": clean_content})

        if len(user_memories[user_id]) > (MAX_MEMORY * 2):
            user_memories[user_id] = user_memories[user_id][-(MAX_MEMORY * 2):]

        api_messages = [{"role": "system", "content": GRACE_PERSONALITY}]
        api_messages.extend(user_memories[user_id])

        async with message.channel.typing():
            try:
                response = await grok_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=api_messages
                )
                bot_reply = response.choices[0].message.content
                user_memories[user_id].append({"role": "assistant", "content": bot_reply})
                await message.reply(bot_reply)
            except Exception as e:
                print(f"Error: {e}")
                if len(user_memories[user_id]) > 0:
                    user_memories[user_id].pop()
                await message.reply("Aduh, otak aku lagi ngeblank nih. Coba lagi ya! 😵")

    await bot.process_commands(message)

# ==========================================
# COMMANDS
# ==========================================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def hapus(ctx, jumlah: int):
    """Menghapus sejumlah pesan di channel"""
    if jumlah > 100:
        await ctx.send("Waduh, kebanyakan! Maksimal hapus 100 pesan aja ya sekali jalan. 😵")
        return

    deleted = await ctx.channel.purge(limit=jumlah + 1)
    notif = await ctx.send(f"🧹 Bip boop! Miu udah menyingkirkan {len(deleted)-1} pesan buat kamu.")
    await notif.delete(delay=5)

@hapus.error
async def hapus_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Eh, kasih tau dong berapa pesan yang mau dihapus! Contoh: `Miu hapus 10` 🧐")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Eits, kamu nggak punya izin buat hapus pesan di server ini! 😝")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Jumlah pesannya harus pakai angka ya, jangan pakai huruf!")

# ==========================================
# 3. JALANKAN WEB SERVER & BOT
# ==========================================
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
