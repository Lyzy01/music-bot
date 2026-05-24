import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import asyncio
from keep_alive import keep_alive

# 1. Setup
TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIFY_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIFY_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET)
sp = spotipy.Spotify(auth_manager=auth_manager)

intents = discord.Intents.default()
intents.message_content = True 
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. Options
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch',
    'nocheckcertificate': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    }
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# 3. Sync Command (For DMs/Global)
@bot.command()
@commands.is_owner()
async def sync(ctx):
    try:
        await bot.tree.sync()
        await ctx.send("🌍 Global Sync Complete! Commands will appear in DMs soon.")
    except Exception as e:
        await ctx.send(f"❌ Sync Error: {e}")

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} is online!')
    await bot.tree.sync()

# 4. The Play Command
@bot.tree.command(name="play", description="Play music (Works in DMs!)")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()

    # Find where the user is
    user_vc = None
    guild_to_join = None
    for guild in bot.guilds:
        member = guild.get_member(interaction.user.id)
        if member and member.voice:
            user_vc = member.voice.channel
            guild_to_join = guild
            break

    if not user_vc:
        return await interaction.followup.send("❌ Join a Voice Channel in a server first!")

    # Connect
    vc = guild_to_join.voice_client
    if not vc:
        vc = await user_vc.connect()
    elif vc.channel != user_vc:
        await vc.move_to(user_vc)

    # Search Logic
    query = search
    if "spotify.com" in search:
        try:
            track = sp.track(search)
            query = f"{track['name']} {track['artists'][0]['name']}"
        except:
            return await interaction.followup.send("❌ Spotify error. Check API keys!")

    try:
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
            url = info['url']
            title = info['title']

        # THE FIX: Explicitly calling 'ffmpeg'
        source = await discord.FFmpegOpusAudio.from_probe(url, executable="ffmpeg", **FFMPEG_OPTIONS)
        
        if vc.is_playing():
            vc.stop()
        
        vc.play(source)
        await interaction.followup.send(f"🎶 Playing in **{guild_to_join.name}**: `{title}`")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}")

@bot.tree.command(name="leave", description="Make the bot leave voice")
async def leave(interaction: discord.Interaction):
    for vc in bot.voice_clients:
        if interaction.user in vc.channel.members:
            await vc.disconnect()
            return await interaction.response.send_message("👋 Left the channel!")
    await interaction.response.send_message("❌ You aren't in a voice channel with me.")

keep_alive()
bot.run(TOKEN)
