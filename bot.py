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

auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

# 2. Bot & Intents
intents = discord.Intents.default()
intents.message_content = True 
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 3. YouTube & FFmpeg Options
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

# 5. Commands (UPDATED SYNC COMMAND ADDED HERE)
@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Force syncs slash commands to the current server immediately"""
    try:
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"⚡ Forced sync {len(synced)} commands to this server!")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

@bot.tree.command(name="play", description="Play music from Spotify or YouTube")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()

    if not interaction.user.voice:
        return await interaction.followup.send("❌ Join a voice channel first!")
    
    vc = interaction.guild.voice_client
    if not vc:
        vc = await interaction.user.voice.channel.connect()

    final_query = search
    if "spotify.com" in search:
        try:
            track = sp.track(search)
            final_query = f"{track['name']} {track['artists'][0]['name']}"
        except:
            return await interaction.followup.send("❌ Spotify link error.")

    try:
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{final_query}", download=False)['entries'][0]
            url = info['url']
            title = info['title']

        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        
        if vc.is_playing():
            vc.stop()

        vc.play(source)
        await interaction.followup.send(f"🎶 Now Playing: **{title}**")

    except Exception as e:
        await interaction.followup.send("❌ Error finding that song.")

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
