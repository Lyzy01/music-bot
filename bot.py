import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import asyncio
from keep_alive import keep_alive

# 1. Setup & Environment Variables (Pulled from Render)
TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIFY_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIFY_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# Authenticate Spotify
auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# 2. Bot & Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 3. Optimized Audio Options for 2026
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
}

# FFmpeg settings to prevent "Choppy" audio or mid-song stops
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# 4. Events
@bot.event
async def on_ready():
    print(f'✅ Bot is online: {bot.user.name}')
    try:
        synced = await bot.tree.sync()
        print(f"⚡ Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"Sync error: {e}")

# 5. The Play Command
@bot.tree.command(name="play", description="Play music from Spotify or YouTube")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()

    # Join VC logic
    if not interaction.user.voice:
        return await interaction.followup.send("❌ Join a voice channel first!")
    
    vc = interaction.guild.voice_client
    if not vc:
        vc = await interaction.user.voice.channel.connect()

    # Spotify Link Detection
    final_search = search
    display_name = "Searching..."
    
    if "spotify.com" in search:
        try:
            track_info = sp.track(search)
            final_search = f"{track_info['name']} {track_info['artists'][0]['name']}"
            display_name = f"{track_info['name']} by {track_info['artists'][0]['name']}"
        except Exception:
            return await interaction.followup.send("❌ Error reading Spotify link. Is your Client ID/Secret correct?")

    # Fetch Audio
    try:
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{final_search}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title = info.get('title', display_name)

        # Use FFmpegOpusAudio for better quality in 2026
        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        
        if vc.is_playing():
            vc.stop()

        vc.play(source)
        await interaction.followup.send(f"🎶 Now Playing: **{title}**")

    except Exception as e:
        print(f"Play error: {e}")
        await interaction.followup.send("❌ I couldn't find or play that song. YouTube might be blocking me!")

@bot.tree.command(name="leave", description="Kick the bot from voice")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Bye bye!")
    else:
        await interaction.response.send_message("I'm not in a channel!")

# 6. Keep-Alive & Run
keep_alive()
bot.run(TOKEN)
