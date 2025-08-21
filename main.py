import discord
from discord.ext import commands
from discord import app_commands
import subprocess
import json
import psutil
import platform
import time
import yt_dlp
import asyncio
import os

# --- Configuration ---
TOKEN = os.getenv("dc_token")

def load_radio_stations(file_path):
    stations = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                id, name, url = line.split(';')
                id = int(id.split(': ')[1].strip())
                name = name.split(': ')[1].strip()
                url = url.split(': ')[1].strip()
                stations[id] = {'name': name, 'url': url}
                stations[name.lower()] = {'id': id, 'url': url}
    return stations

def create_url(station_id):
    return f"https://open.fm/api/user/token?fp=https://stream-cdn-1.open.fm/OFM{station_id}/ngrp:standard/playlist.m3u8"

def fetch_url_from_api(url):
    try:
        curl_command = ["curl", "-s", url]
        response = subprocess.check_output(curl_command).decode("utf-8")
        data = json.loads(response)
        return data.get("url", None)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error fetching URL: {e}")
        return None

def fetch_openfm_stream_url(station_id):
    url = create_url(station_id)
    return fetch_url_from_api(url)

def load_openfm_stations():
    openfm_stations = {
        8: {"name": "Open FM - Vixa", "id": 207},
        9: {"name": "Open FM - Dance", "id": 160},
        10: {"name": "Open FM - Do Auta", "id": 163},
        11: {"name": "Open FM - 500 Party Hits", "id": 169},
    }
    for id, station in openfm_stations.items():
        stream_url = fetch_openfm_stream_url(station["id"])
        if stream_url:
            RADIO_STATIONS[id] = {"name": station["name"], "url": stream_url}
            RADIO_STATIONS[station["name"].lower()] = {"id": id, "url": stream_url}

RADIO_STATIONS = load_radio_stations('stacje.txt')
load_openfm_stations()
DEFAULT_VOLUME = 1.0

# --- Setup ---
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix='!', intents=intents)

ffmpeg_options = {
    'options': '-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
}

# --- Global Variables ---
voice_client = None
current_station = None
volume = DEFAULT_VOLUME
start_time = time.time()
previous_station = None
current_song_title = None
current_song_url = None
youtube_queue = []  # globalna kolejka utworów
# Usuwamy zmienną playlist_remainder i dodajemy:
current_playlist_url = None  # adres bieżącej playlisty
playlist_next_index = 1     # indeks następnego utworu do pobrania

# --- Bot Events ---
@bot.event
async def on_ready():
    print(f'Bot zalogowany jako {bot.user.name} ({bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Game(name=f"Gotowy do Grania!"))
    await bot.tree.sync()

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """Handles voice state updates for all members"""
    global voice_client, current_station, current_song_title, current_song_url
    
    if voice_client and voice_client.channel:
        # Policz ilość członków na kanale (nie licząc botów)
        members = len([m for m in voice_client.channel.members if not m.bot])
        
        # Jeśli bot został sam na kanale
        if members == 0:
            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            voice_client = None
            current_station = None
            current_song_title = None
            current_song_url = None
            await bot.change_presence(activity=discord.Game(name=f"Gotowy do Grania!"))

# --- Helper Functions ---
async def connect_to_voice_channel(ctx):
    """Connects to the voice channel of the command sender."""
    global voice_client
    if ctx.author.voice is None:
        await ctx.send("❌ Musisz być na kanale głosowym, aby użyć tej komendy.")
        return False

    voice_channel = ctx.author.voice.channel
    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)
    return True

async def disconnect_from_voice_channel(ctx):
    """Disconnects the bot from the voice channel."""
    global voice_client, current_station
    if voice_client is not None:
        await voice_client.disconnect()
        voice_client = None
        current_station = None
        await bot.change_presence(activity=discord.Game(name=f"Gotowy do Grania!"))
        await ctx.send("🔌 Odłączono od kanału głosowego.")
    else:
        await ctx.send("❌ Nie jestem połączony z żadnym kanałem głosowym.")

async def play_radio(ctx, station_url, station_name):
    """Plays the radio station in the voice channel."""
    global voice_client, current_station, volume, current_song_title, current_song_url

    if voice_client is None or not voice_client.is_connected():
        connected = await connect_to_voice_channel(ctx)
        if not connected:
            return

    if voice_client.is_playing():
        voice_client.stop()

    try:
        audio_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(station_url, **ffmpeg_options), volume=volume)
        voice_client.play(audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(handle_playback_error(e, ctx, station_url, station_name), bot.loop) if e else None)
        current_station = station_name
        current_song_title = None
        current_song_url = None
        await bot.change_presence(activity=discord.Game(name=f"Gra: {station_name}"))
        if not ctx.interaction.response.is_done():
            await ctx.interaction.response.send_message(f"🎶 Teraz grane: **{station_name}**")

    except Exception as e:
        print(f"Błąd odtwarzania radia: {e}")
        if not ctx.interaction.response.is_done():
            await ctx.interaction.response.send_message(f"❌ Nie udało się odtworzyć stacji radiowej. Błąd: `{e}`")

async def handle_playback_error(error, ctx, station_url, station_name):
    """Handles playback errors."""
    if error:
        print(f"Błąd odtwarzania: {error}")
        # Ponowne połączenie w przypadku błędu
        await asyncio.sleep(5)  # Odczekaj 5 sekund przed ponownym połączeniem
        await play_radio(ctx, station_url, station_name)

# --- Autocomplete ---
async def play_autocomplete(interaction: discord.Interaction, current: str):
    return [
        discord.app_commands.Choice(name=station['name'], value=str(id))
        for id, station in RADIO_STATIONS.items()
        if isinstance(id, int) and current.lower() in station['name'].lower()
    ][:25]

@bot.tree.command(name='leave', description='Opuszcza kanał głosowy.')
async def leave_command(interaction: discord.Interaction):
    """Leaves the voice channel and stops playing."""
    ctx = await bot.get_context(interaction)
    await disconnect_from_voice_channel(ctx)
    if not interaction.response.is_done():
        await interaction.response.send_message("🔌 Odłączono od kanału głosowego.")

@bot.tree.command(name='play', description='Odtwarza stację radiową.')
@app_commands.autocomplete(station_identifier=play_autocomplete)
async def play_command(interaction: discord.Interaction, station_identifier: str):
    """Plays a specific radio station."""
    ctx = await bot.get_context(interaction)
    global current_station

    try:
        station_id = int(station_identifier)
        if station_id in RADIO_STATIONS:
            station = RADIO_STATIONS[station_id]
            await play_radio(ctx, station['url'], station['name'])
            if not interaction.response.is_done():
                await interaction.response.send_message(f"🎶 Teraz grane: **{station['name']}**")
        else:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Stacja o ID '{station_id}' nie została znaleziona. Użyj `/stations`, aby zobaczyć dostępne stacje.")
    except ValueError:
        station_name_lower = station_identifier.lower()
        if station_name_lower in RADIO_STATIONS:
            station = RADIO_STATIONS[station_name_lower]
            await play_radio(ctx, station['url'], station_identifier)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"🎶 Teraz grane: **{station_identifier}**")
        else:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Stacja '{station_identifier}' nie została znaleziona. Użyj `/stations`, aby zobaczyć dostępne stacje.")


@bot.tree.command(name='stacje', description='Wyświetla dostępne stacje radiowe.')
async def stations_command(interaction: discord.Interaction):
    """Lists the available radio stations."""
    station_list = "\n".join([f"- {id} - **{station['name']}**" for id, station in RADIO_STATIONS.items() if isinstance(id, int)])
    if not interaction.response.is_done():
        await interaction.response.send_message(f"📻 Dostępne stacje radiowe:\n{station_list}\n\nUżyj `/play`, aby odtworzyć stację.")

@bot.tree.command(name='volume', description='Ustawia poziom głośności (0-200).')
async def volume_command(interaction: discord.Interaction, vol: int):
    """Sets the volume of the player."""
    ctx = await bot.get_context(interaction)
    global volume
    if vol is None:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"🔊 Aktualna głośność to **{int(volume * 100)}%**.")
        return

    if not 0 <= vol <= 200:
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Głośność musi być w zakresie od 0 do 200.")
        return

    volume = vol / 100.0
    if voice_client and voice_client.source:
        voice_client.source.volume = volume
        if not interaction.response.is_done():
            await interaction.response.send_message(f"🔊 Ustawiono głośność na **{vol}%**.")
    else:
        if not interaction.response.is_done():
            await interaction.response.send_message("🔊 Głośność ustawiona dla przyszłego odtwarzania. Dołącz do kanału głosowego i odtwórz stację, aby zastosować głośność.")

@bot.tree.command(name='terazgrane', description='Pokazuje aktualnie odtwarzaną stację radiową lub utwór z YouTube.')
async def nowplaying_command(interaction: discord.Interaction):
    """Shows the currently playing radio station."""
    global current_station, current_song_title, current_song_url
    if current_station or current_song_title:
        if current_song_title and current_song_url:
            await interaction.response.send_message(f"🎶 Teraz grane: **{current_song_title}** - [Link]({current_song_url})")
        else:
            await interaction.response.send_message(f"🎶 Teraz grane: **{current_station}**")
    else:
        await interaction.response.send_message("❌ Nic nie jest aktualnie odtwarzane.")

@bot.tree.command(name='performance', description='Pokazuje statystyki systemu i bota.')
async def stats_command(interaction: discord.Interaction):
    """Shows system and bot statistics."""
    ctx = await bot.get_context(interaction)
    uptime = time.time() - start_time
    uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime))
    
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')
    
    system_info = platform.uname()
    cpu_model = subprocess.check_output("lscpu | grep 'Model name'", shell=True).decode()
    cpu_model = cpu_model.replace('BIOS Model name:', '').replace('Model name:', '').replace('\n', ' ').strip()
    cpu_model = ' '.join(cpu_model.split())
    
    cpu_cores = psutil.cpu_count(logical=False)
    cpu_threads = psutil.cpu_count(logical=True)
    
    stats_message = (
        f"**Statystyki systemu i bota:**\n \n"
        f"🖥️ **System operacyjny:** {system_info.system} {system_info.release}\n"
        f"🌐 **Platforma:** Google Cloud Platform \n"
        f"💻 **Procesor:** {cpu_model} (Rdzenie: {cpu_cores}, Wątki: {cpu_threads})\n"
        f"⚙️ **Zużycie procesora:** {cpu_usage}%\n"
        f"🧠 **Zużycie pamięci:** {memory_info.percent}% ({memory_info.used // (1024 ** 2)}MB / {memory_info.total // (1024 ** 2)}MB)\n"
        f"💾 **Zużycie dysku:** {disk_usage.percent}%\n" 
        f"📍 **Lokalizacja serwera:** Warszawa\n"
        f"⏱️ **Uptime bota:** {uptime_str}\n"
    )
    
    if not interaction.response.is_done():
        await interaction.response.send_message(stats_message)

async def get_youtube_info(url):
    """Asynchronicznie pobiera informacje o filmie lub playliście z YouTube."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': False,
        'quiet': True,
        'default_search': 'ytsearch',
        'extract_flat': True,
        # Dodatkowe opcje, aby obejść weryfikację
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': True,
        'cookiefile': None,  # Brak pliku cookie
        'extractor_args': {'youtube': {'skip': ['dash', 'hls']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'pl-PL,pl;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
    }
    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
            if 'entries' in info:
                if len(info['entries']) == 1:
                    info = info['entries'][0]
            return info
    except Exception as e:
        print(f"Błąd podczas pobierania informacji z YouTube: {e}")
        return None

async def play_youtube_track(ctx, info):
    """Odtwarza pojedynczy utwór z YouTube."""
    global voice_client, current_song_title, current_song_url, volume
    
    # Pobieranie bezpośredniego URL audio z info lub ponowne pobranie pełnych informacji
    try:
        if 'url' not in info or info.get('is_live', False):
            # Dla transmisji na żywo lub gdy brakuje bezpośredniego URL
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'nocheckcertificate': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                }
            }
            loop = asyncio.get_event_loop()
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                detailed_info = await loop.run_in_executor(None, lambda: ydl.extract_info(info['webpage_url'] if 'webpage_url' in info else info['url'], download=False))
                stream_url = detailed_info['url']
        else:
            stream_url = info['url']
        
        print(f"DEBUG: Przekazywany URL do FFmpeg: {stream_url}")
        
        ffmpeg_options_adjusted = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn -bufsize 16M'  # Zwiększony bufor
        }

        if voice_client.is_playing():
            voice_client.stop()
        audio_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(stream_url, **ffmpeg_options_adjusted), volume=volume)
        voice_client.play(audio_source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_in_queue(ctx), bot.loop))
        current_song_title = info.get('title', 'Nieznany tytuł')
        current_song_url = info.get('webpage_url', 'Brak URL')
        await bot.change_presence(activity=discord.Game(name=f"Gra z YouTube"))
        if ctx and not ctx.interaction.response.is_done():
            asyncio.run_coroutine_threadsafe(ctx.interaction.followup.send(f"🎶 Teraz grane: **[{current_song_title}]({current_song_url})**"), bot.loop)
    except Exception as e:
        print(f"DEBUG: Błąd odtwarzania: {e}")
        if ctx and not ctx.interaction.response.is_done():
            asyncio.run_coroutine_threadsafe(ctx.interaction.followup.send(f"❌ Wystąpił błąd podczas odtwarzania: {str(e)}"), bot.loop)

async def play_next_in_queue(ctx):
    """Odtwarza kolejny utwór w kolejce.
    Jeśli kolejka zawiera mniej niż 2 utwory i mamy adres playlisty, pobiera tylko jeden kolejny utwór."""
    global youtube_queue, current_playlist_url, playlist_next_index, previous_station
    if current_playlist_url and len(youtube_queue) < 2:
        new_track = await fetch_playlist_batch(current_playlist_url, playlist_next_index, playlist_next_index)
        if new_track:
            youtube_queue.extend(new_track)
            playlist_next_index += len(new_track)
    if youtube_queue:
        next_info = youtube_queue.pop(0)
        await play_youtube_track(ctx, next_info)
    else:
        # Jeśli kolejka pusta, przywróć poprzednią stację (jeśli zapamiętana)
        await after_youtube_playback()


@bot.tree.command(name='yt', description='Odtwarza utwór lub playlistę z YouTube.')
async def yt_command(interaction: discord.Interaction, url: str):
    await interaction.response.defer()  # Informuje Discord, że odpowiedź może zająć więcej czasu
    ctx = await bot.get_context(interaction)
    global previous_station, current_song_title, current_song_url, youtube_queue, current_playlist_url, playlist_next_index

    if not await connect_to_voice_channel(ctx):
        await interaction.followup.send("❌ Nie można połączyć z kanałem głosowym.")
        return

    info = await get_youtube_info(url)
    if not info:
        await interaction.followup.send("❌ Nie udało się pobrać informacji o filmie lub playliście.")
        return

    print("DEBUG: Pełne info po get_youtube_info(url):")
    print(json.dumps(info, indent=4)) # LOGOWANIE CAŁEGO 'info'

    # Jeżeli to playlista
    if 'entries' in info and len(info['entries']) > 1:
        current_playlist_url = url
        playlist_next_index = 2  # Zaczynamy od drugiego utworu, bo pierwszy odtwarzamy od razu
        first_song_info = info['entries'][0] # Pobierz info o PIERWSZYM utworze

        print("\nDEBUG: Pełne first_song_info:")
        print(json.dumps(first_song_info, indent=4)) # LOGOWANIE CAŁEGO 'first_song_info'

        youtube_queue.extend(info['entries'][1:])  # Dodajemy resztę utworów do kolejki
        await play_youtube_track(ctx, first_song_info)  # Odtwarzamy PIERWSZY UTWÓR od razu (używając jego info)
        await interaction.followup.send(f"✅ Dodano do kolejki **{len(info['entries']) - 1}** utworów z playlisty. Aktualnie gramy pierwszy utwór.")
        # Pobieramy resztę utworów w tle
        asyncio.create_task(fetch_remaining_playlist_tracks())
    else:
        # Pojedynczy utwór
        if isinstance(info, dict) and 'entries' in info:
            info = info['entries'][0]
        await play_youtube_track(ctx, info)
        await interaction.followup.send(f"🎶 Teraz grane: **[{info.get('title', 'Nieznany tytuł')}]({info.get('webpage_url', 'Brak URL')})**")

async def fetch_remaining_playlist_tracks():
    """Pobiera resztę utworów z playlisty w tle."""
    global current_playlist_url, playlist_next_index, youtube_queue
    while current_playlist_url:
        new_tracks = await fetch_playlist_batch(current_playlist_url, playlist_next_index, playlist_next_index + 49)
        if not new_tracks:
            break
        youtube_queue.extend(new_tracks)
        playlist_next_index += len(new_tracks)

async def after_youtube_playback():
    """Obsługuje zakończenie odtwarzania utworu z YouTube."""
    global previous_station, current_song_title, current_song_url
    if youtube_queue:
        # Kolejny utwór zostanie odtworzony w play_next_in_queue
        return
    if previous_station:
        station = RADIO_STATIONS.get(previous_station)
        if station:
            # Wywołanie play_radio bez kontekstu, jeżeli poprzednia stacja była radiowa
            await play_radio(None, station['url'], station['name'])
        previous_station = None
    else:
        current_song_title = None
        current_song_url = None
        current_station = None
        await bot.change_presence(activity=discord.Game(name=f"Gotowy do Grania!"))

@bot.tree.command(name='kolejka', description='Wyświetla aktualną kolejkę muzyki.')
async def queue_command(interaction: discord.Interaction):
    """Displays the current YouTube music queue."""
    global youtube_queue
    if youtube_queue:
        queue_list = "\n".join(
            f"{idx}. {track.get('title', 'Nieznany tytuł')}" for idx, track in enumerate(youtube_queue, start=1)
        )
        await interaction.response.send_message(f"🎶 Aktualna kolejka muzyki:\n{queue_list}")
    else:
        await interaction.response.send_message("ℹ️ Kolejka jest pusta.")

@bot.tree.command(name='skip', description='Pomija aktualnie odtwarzany utwór.')
async def skip_command(interaction: discord.Interaction):
    """Skips the currently playing track."""
    ctx = await bot.get_context(interaction)
    global voice_client
    if voice_client and voice_client.is_playing():
        voice_client.stop()  # wywoła callback, który odtworzy kolejny utwór
        await interaction.response.send_message("⏭️ Pominięto utwór.")
    else:
        await interaction.response.send_message("❌ Nie ma aktualnie odtwarzanego utworu.")

async def fetch_playlist_batch(playlist_url, start, end):
    """Pobiera fragment playlisty między start a end (włącznie)"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': False,
        'quiet': True,
        'playlist_items': f"{start}-{end}",
        'default_search': 'ytsearch',
        # Dodatkowe opcje obejścia ograniczeń
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'skip': ['dash', 'hls']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'pl-PL,pl;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
    }
    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(playlist_url, download=False))
            if 'entries' in info:
                return info['entries']
            return []
    except Exception as e:
        print(f"Błąd podczas pobierania fragmentu playlisty: {e}")
        return []

# --- Run the bot ---
if __name__ == "__main__":
    bot.run(TOKEN)
