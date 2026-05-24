import os
import discord
from discord.ext import commands
import yt_dlp
import asyncio
from keep_alive import keep_alive

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration for yt-dlp (extracts audio only)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'nocheckcertificate': True,
}

# Configuration for FFmpeg (handles the audio stream processing)
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

@bot.event
async def on_ready():
    print(f'⚡ {bot.user.name} is connected to Discord Voice systems!')

@bot.command()
async def join(ctx):
    """Makes the bot join your current voice channel"""
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await ctx.voice_client.connect()
    else:
        await ctx.send("❌ You need to join a voice channel first!")

@bot.command()
async def play(ctx, *, search: str):
    """Plays audio from YouTube: !play [song name or video URL]"""
    if not ctx.voice_client:
        await ctx.invoke(join)
        
    if not ctx.voice_client:
        return

    await ctx.send(f"🔍 Searching YouTube for: **{search}**...")

    # Extract audio link asynchronously so the bot doesn't freeze
    loop = asyncio.get_event_loop()
    try:
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
    except Exception as e:
        await ctx.send("❌ Failed to process or find that song.")
        print(e)
        return

    # Grab the first video result if a search term was used
    if 'entries' in data:
        info = data['entries'][0]
    else:
        info = data

    url = info['url']
    title = info['title']

    # If something is already playing, stop it first
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    # Pass the stream link into FFmpeg and play it in Discord
    audio_source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
    ctx.voice_client.play(audio_source)
    
    await ctx.send(f"🎶 Now playing: **{title}**")

@bot.command()
async def pause(ctx):
    """Pauses the current song"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Music paused.")

@bot.command()
async def resume(ctx):
    """Resumes a paused song"""
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Music resumed.")

@bot.command()
async def leave(ctx):
    """Disconnects the bot from the voice channel"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left the voice channel.")
    else:
        await ctx.send("❌ I am not in a voice channel.")

# Fire up the background web server
keep_alive()

# Start the bot
bot.run(os.getenv('DISCORD_TOKEN'))
