import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import asyncio
from keep_alive import keep_alive

# 1. Setup & Environment Variables
TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIFY_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIFY_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# Authenticate Spotify
auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# 2. Bot & Intents (CRITICAL: These must be ON in Discord Dev Portal too)
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 3. Enhanced YouTube Options (To bypass blocks)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'nocheckcertificate': True,
    'no_warnings': True,
    'extract_flat': True,
    'source_address': '0.0.0.0',
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# 4. Events
@bot.event
async def on_ready():
    print(f'✅ Bot Online: {bot.user.name}')
    await bot.tree.sync() # Auto-syncs commands on start

# 5. Commands
@bot.tree.command(name="play", description="Play music from Spotify or YouTube")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()

    if not interaction.user.voice:
        return await interaction.followup.send("❌ Join a voice channel first!")
    
    vc = interaction.guild.voice_client
    if not vc:
        vc = await interaction.user.voice.channel.connect()

    # Spotify Link Detection
    final_query = search
    if "spotify.com" in search:
        try:
            track = sp.track(search)
            final_query = f"{track['name']} {track['artists'][0]['name']}"
        except:
            return await interaction.followup.send("❌ Spotify link error. Check your API keys!")

    # Audio Extraction
    try:
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            # We try a few times in case of a temporary block
            info = ydl.extract_info(f"ytsearch:{final_query}", download=False)['entries'][0]
            url = info['url']
            title = info['title']

        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        
        if vc.is_playing():
            vc.stop()

        vc.play(source)
        await interaction.followup.send(f"🎶 Now Playing: **{title}**")

    except Exception as e:
        print(f"YTDL Error: {e}")
        await interaction.followup.send("❌ Error finding that song. YouTube might be blocking the bot's IP!")

@bot.tree.command(name="leave", description="Make the bot leave voice")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Left the channel!")
    else:
        await interaction.response.send_message("I'm not in a channel!")

# 6. Run
keep_alive()
bot.run(TOKEN)
