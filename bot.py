import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import asyncio
from keep_alive import keep_alive

# 1. Setup & Authentication
TOKEN = os.getenv('DISCORD_TOKEN')
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET')
))

# 2. Bot Configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 3. Music Player Options
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'nocheckcertificate': True,
    'no_warnings': True,
    'source_address': '0.0.0.0',
    'extract_flat': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# 4. Events
@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"⚡ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Error syncing: {e}")

# 5. Slash Commands
@bot.tree.command(name="play", description="Play music from Spotify or YouTube")
@app_commands.describe(search="Song name or link")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()

    # Join Voice Channel
    if not interaction.user.voice:
        return await interaction.followup.send("❌ You need to be in a voice channel!")
    
    vc = interaction.guild.voice_client
    if not vc:
        vc = await interaction.user.voice.channel.connect()

    # Handle Spotify Links
    display_name = search
    if "open.spotify.com/track/" in search:
        try:
            track = sp.track(search)
            search = f"{track['name']} {track['artists'][0]['name']}"
            display_name = f"{track['name']} by {track['artists'][0]['name']}"
        except Exception as e:
            return await interaction.followup.send("❌ Could not read that Spotify link.")

    # Search and Stream
    try:
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{search}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title = info.get('title', display_name)

        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        
        if vc.is_playing():
            vc.stop()

        vc.play(source)
        await interaction.followup.send(f"🎶 Playing: **{title}**")

    except Exception as e:
        print(f"Play Error: {e}")
        await interaction.followup.send("❌ Error finding or playing that song.")

@bot.tree.command(name="stop", description="Stop the music and leave")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Stopped and left the channel.")
    else:
        await interaction.response.send_message("I'm not in a voice channel!")

# 6. Manual Sync Command (Prefix)
@bot.command()
@commands.is_owner()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("✅ Slash commands synced!")

# 7. Start the Bot
keep_alive() # Starts the Flask web server
bot.run(TOKEN)
