import os
import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import asyncio
from keep_alive import keep_alive

# 1. Setup Bot with a command prefix (only used for the !sync command)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'ytsearch', # Change this to 'scsearch' if YouTube keeps failing
    'nocheckcertificate': True,
    'quiet': True,
}

@bot.event
async def on_ready():
    print(f'⚡ {bot.user.name} is online and ready for Slash Commands!')

# --- THE SYNC COMMAND (Run this once in Discord to activate / commands) ---
@bot.command()
@commands.is_owner()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("✅ Slash commands synced to all servers!")

# --- SLASH COMMANDS ---

@bot.tree.command(name="join", description="Makes the bot join your voice channel")
async def join(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        await interaction.response.send_message(f"Connected to **{channel.name}**!")
    else:
        await interaction.response.send_message("❌ Join a voice channel first!", ephemeral=True)

@bot.tree.command(name="play", description="Play a song from YouTube")
@app_commands.describe(search="The song name or YouTube link")
async def play(interaction: discord.Interaction, search: str):
    # This command takes time, so we "defer" the response to avoid a timeout error
    await interaction.response.defer()

    if not interaction.guild.voice_client:
        if interaction.user.voice:
            await interaction.user.voice.channel.connect()
        else:
            await interaction.followup.send("❌ Join a voice channel first!")
            return

    # Search for the song
    loop = asyncio.get_event_loop()
    try:
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
        info = data['entries'][0] if 'entries' in data else data
        url, title = info['url'], info['title']

        if interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()

        interaction.guild.voice_client.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
        await interaction.followup.send(f"🎶 Now playing: **{title}**")
    except Exception as e:
        await interaction.followup.send("❌ Error finding that song.")
        print(e)

@bot.tree.command(name="stop", description="Stop the music and leave")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Left the voice channel.")
    else:
        await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)

@bot.tree.command(name="pause", description="Pause the current song")
async def pause(interaction: discord.Interaction):
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.pause()
        await interaction.response.send_message("⏸️ Music paused.")
    else:
        await interaction.response.send_message("Nothing is playing.", ephemeral=True)

@bot.tree.command(name="resume", description="Resume the current song")
async def resume(interaction: discord.Interaction):
    if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
        interaction.guild.voice_client.resume()
        await interaction.response.send_message("▶️ Music resumed.")
    else:
        await interaction.response.send_message("The music isn't paused.", ephemeral=True)

# Start web server & bot
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
