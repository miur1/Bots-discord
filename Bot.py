import os
import discord
from discord.ext import commands
from google import genai

# Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Setup Gemini Client
# Catatan: Di versi library google-genai terbaru, kita pakai genai.Client()
ai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@bot.event
async def on_ready():
    print(f'Bot chat {bot.user} udah siap nemenin kamu ngobrol! 🤖✨')

@bot.event
async def on_message(message):
    # Biar bot gak bales chat-nya sendiri
    if message.author == bot.user:
        return

    # Bot bakal ngerespon kalau namanya dimention (@Bot)
    if bot.user.mentioned_in(message):
        # Ambil teks chat setelah mention namanya
        user_prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if not user_prompt:
            await message.reply("Kenapa manggil-manggil? Kangen ya?😜")
            return

        async with message.channel.typing():
            try:
                # Minta tolong Gemini buat mikir jawabannya
                # Kamu bisa tambahin system_instruction biar kepribadiannya mirip kamu atau aku!
                response = ai_client.models.generate_content(
                    model='grok-4.3',
                    contents=user_prompt,
                )
                await message.reply(response.text)
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("Aduh, otak aku lagi ngeblank nih. Coba tanya lagi nanti ya! 😵")

    await bot.process_commands(message)
  
