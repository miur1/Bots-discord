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
from datetime import datetime, timedelta


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

user_stats = {}

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
    # LOGIKA LEVELING & PENDAPATAN GOLD
    # ==========================================
    user_id = message.author.id
    
    # Bikin profil baru kalau user belum terdaftar
    if user_id not in user_stats:
        user_stats[user_id] = {"xp": 0, "level": 1, "gold": 0, "inventory": [], "last_daily": None}
    
    # Setiap kirim pesan dapat 10 XP
    user_stats[user_id]["xp"] += 10
    
    # Rumus batas XP naik level: (Level x 100)
    batas_xp = user_stats[user_id]["level"] * 100
    
    if user_stats[user_id]["xp"] >= batas_xp:
        user_stats[user_id]["level"] += 1
        user_stats[user_id]["xp"] = 0 # Reset XP setelah naik level
        
        # Hadiah Gold setiap naik level
        hadiah_gold = user_stats[user_id]["level"] * 50
        user_stats[user_id]["gold"] += hadiah_gold
        
        await message.channel.send(f"🎉 Wuih! {message.author.mention} rajin banget nge-chat, sekarang naik ke **Level {user_stats[user_id]['level']}**! Miu kasih hadiah **{hadiah_gold} Gold** buat modal gacha! 💰")
        

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
    if bot.user and bot.user.mentioned_in(message):
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
# COMMAND SISTEM GOLD & GACHA
# ==========================================

@bot.command()
async def profil(ctx):
    """Melihat level, gold, dan tas kamu"""
    user_id = ctx.author.id
    if user_id not in user_stats:
        await ctx.send("Kamu belum punya profil. Ngobrol dulu dong di sini biar dapet XP! 😝")
        return
        
    stats = user_stats[user_id]
    
    teks = f"**📊 Profil {ctx.author.name}**\n"
    teks += f"⭐ Level: {stats['level']}\n"
    teks += f"✨ XP: {stats['xp']} / {stats['level'] * 100}\n"
    teks += f"💰 Gold: {stats['gold']}G\n"
    
    isi_tas = ", ".join(stats['inventory']) if stats['inventory'] else "Kosong melompong, gacha makanya!"
    teks += f"🎒 Tas: {isi_tas}"
    
    await ctx.send(teks)

@bot.command()
async def daily(ctx):
    """Klaim jatah Gold gratis setiap 24 jam"""
    user_id = ctx.author.id
    if user_id not in user_stats:
        user_stats[user_id] = {"xp": 0, "level": 1, "gold": 0, "inventory": [], "last_daily": None}
    
    sekarang = datetime.now()
    waktu_terakhir = user_stats[user_id]["last_daily"]
    
    # Cek apakah sudah lewat 24 jam sejak klaim terakhir
    if waktu_terakhir and (sekarang - waktu_terakhir) < timedelta(days=1):
        sisa_waktu = timedelta(days=1) - (sekarang - waktu_terakhir)
        jam, sisa = divmod(sisa_waktu.seconds, 3600)
        menit, detik = divmod(sisa, 60)
        await ctx.send(f"Eits, maruk! Kamu udah ambil jatah hari ini. Tunggu **{jam} jam {menit} menit** lagi ya! ⏳")
        return
        
    # Berikan 150 Gold gratis
    user_stats[user_id]["gold"] += 150
    user_stats[user_id]["last_daily"] = sekarang
    await ctx.send(f"✅ Mantap! {ctx.author.mention} berhasil klaim **150 Gold** harian. Jangan dipakai judi semua ya! 💸")

@bot.command()
async def gacha(ctx):
    """Gacha item menggunakan Gold"""
    user_id = ctx.author.id
    harga_gacha = 10 # Harga per tarikan
    
    if user_id not in user_stats or user_stats[user_id]["gold"] < harga_gacha:
        await ctx.send(f"Yee, miskin! Gold kamu kurang. Butuh **{harga_gacha} Gold** buat gacha. Ketik `Miu daily` dulu sana! 😝")
        return

    # Potong Gold
    user_stats[user_id]["gold"] -= harga_gacha

    # Daftar Item (Rarity, Nama Item, Persentase Peluang)
    pool_hadiah = [
        ("Ampas", "Batu Kerikil", 45),
        ("Common", "Kopi Sachet", 30),
        ("Rare", "Voucher Diskon Makanan", 15),
        ("Epic", "Gitar Akustik", 8),
        ("Legendary", "Pedang Naga Hitam", 2)
    ]
    
    # Ekstrak item dan peluang
    daftar_item = [item[1] for item in pool_hadiah]
    peluang = [item[2] for item in pool_hadiah]
    
    # Undi item pakai random.choices
    hasil_gacha = random.choices(daftar_item, weights=peluang, k=1)[0]
    rarity = next(item[0] for item in pool_hadiah if item[1] == hasil_gacha)
    
    # Simpan ke tas
    user_stats[user_id]["inventory"].append(hasil_gacha)

    # Reaksi Miu sesuai Rarity
    if rarity == "Ampas":
        await ctx.send(f"🎰 {ctx.author.mention} menarik tuas gacha...\nDan dapetnya... **{hasil_gacha}**. Sabar ya, namanya juga ampas. 🤣 *(Sisa Gold: {user_stats[user_id]['gold']}G)*")
    elif rarity == "Legendary":
        await ctx.send(f"🎰 {ctx.author.mention} menarik tuas gacha...\n🌟 WOAH! HOKI GILA! Kamu dapet item **[LEGENDARY]**: **{hasil_gacha}**!!! 🎉 *(Sisa Gold: {user_stats[user_id]['gold']}G)*")
    else:
        await ctx.send(f"🎰 {ctx.author.mention} menarik tuas gacha...\nLumayan lah! Kamu dapet item **[{rarity}]**: **{hasil_gacha}**! ✨ *(Sisa Gold: {user_stats[user_id]['gold']}G)*")

@bot.command()
async def jual(ctx, *, nama_item: str = None):
    """Menjual item dari tas untuk mendapatkan Gold"""
    user_id = ctx.author.id
    
    # 1. Validasi: Punya profil dan isi tas nggak kosong?
    if user_id not in user_stats or not user_stats[user_id]["inventory"]:
        await ctx.send("Tas kamu aja kosong melompong atau kamu belum terdaftar. Ngobrol dulu sana biar dapet item! 😝")
        return
        
    # 2. Validasi: Menyebutkan nama item nggak?
    if not nama_item:
        await ctx.send("Eh, sebutin dong nama item yang mau dijual! Contoh: `Miu jual Batu Kerikil` 🧐")
        return

    # 3. Daftar Harga Item (Silakan disesuaikan harganya)
    harga_item = {
        "Batu Kerikil": 10,
        "Kopi Sachet": 30,
        "Voucher Diskon Makanan": 80,
        "Gitar Akustik": 300,
        "Pedang Naga Hitam": 1000
    }

    # 4. Cari item di tas (dibuat tidak sensitif huruf besar/kecil biar user gampang ketiknya)
    item_ditemukan = None
    for item_di_tas in user_stats[user_id]["inventory"]:
        if item_di_tas.lower() == nama_item.lower():
            item_ditemukan = item_di_tas
            break # Berhenti mencari kalau sudah ketemu 1

    # 5. Eksekusi penjualan
    if item_ditemukan:
        # Hapus 1 item dari tas (kalau punya 2 Batu Kerikil, cuma 1 yang kejual)
        user_stats[user_id]["inventory"].remove(item_ditemukan)
        
        # Ambil harga item dari daftar, kalau entah kenapa itemnya nggak ada di daftar, hargai 5 Gold
        harga = harga_item.get(item_ditemukan, 5)
        user_stats[user_id]["gold"] += harga
        
        await ctx.send(f"🛍️ Laku! {ctx.author.mention} menjual **{item_ditemukan}** ke pasar loak dan dapet **{harga} Gold**. (Total: {user_stats[user_id]['gold']}G) 💰")
    else:
        await ctx.send(f"Hadeh, halu ya? Kamu nggak punya item **{nama_item}** di dalam tas. Cek dulu pakai `Miu profil`! 🙄")
        

# ==========================================
# 3. JALANKAN WEB SERVER & BOT
# ==========================================
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))


