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
intents.members = True # Needed to find you in other servers
intents.voice_states = True
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
    # We do a global sync once on startup for DMs
    try:
        await bot.tree.sync()
        print("🌍 Global commands synced (Available in DMs)")
    except Exception as e:
        print(f"Sync error: {e}")

# 5. DM-Compatible Commands
@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Run this in DMs to force a global refresh"""
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"🌍 Global sync complete! {len(synced)} commands updated.")
        await ctx.send("💡 Note: Global commands can take up to an hour to appear in DMs.")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

@bot.tree.command(name="play", description="Play music (Can be used in DMs)")
async def play(interaction: discord.Interaction, search: str):
    await interaction.response.defer()

    # FIND THE USER: Loop through all servers the bot is in to find where you are sitting
    user_vc = None
    target_guild = None
    
    for guild in bot.guilds:
        member = guild.get_member(interaction.user.id)
        if member and member.voice:
            user_vc = member.voice.channel
            target_guild = guild
            break

    if not user_vc:
        return await interaction.followup.send("❌ I couldn't find you in any Voice Channel! Make sure you are in a server I am also in.")

    # Connect logic
    vc = target_guild.voice_client
    if not vc:
        vc = await user_vc.connect()
    elif vc.channel != user_vc:
        await vc.move_to(user_vc)

    # Spotify Logic
    final_query = search
    if "spotify.com" in search:
        try:
            track = sp.track(search)
            final_query = f"{track['name']} {track['artists'][0]['name']}"
        except:
            return await interaction.followup.send("❌ Spotify link error.")

    # Play Logic
    try:
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = ydl.extract_info(f"ytsearch:{final_query}", download=False)['entries'][0]
            url = info['url']
            title = info['title']

        source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
        
        if vc.is_playing():
            vc.stop()

        vc.play(source)
        await interaction.followup.send(f"🎶 Playing in **{target_guild.name}**: `{title}`")

    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}")

@bot.tree.command(name="leave", description="Make the bot leave the current voice channel")
async def leave(interaction: discord.Interaction):
    # Find where the bot is currently playing
    for vc in bot.voice_clients:
        if interaction.user in vc.channel.members:
            await vc.disconnect()
            return await interaction.response.send_message(f"👋 Left the channel in {vc.guild.name}")
    
    await interaction.response.send_message("❌ I'm not in a voice channel with you!")

# 6. Run
keep_alive()
bot.run(TOKEN)
