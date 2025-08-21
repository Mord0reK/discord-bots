import discord
from discord.ext import commands, tasks
from discord import app_commands
from mcstatus import JavaServer
import asyncio
import os
from google.cloud import compute_v1
import time
import json
from google.oauth2 import service_account


# Konfiguracja bota
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
mc_ip = os.getenv('mc_ip')
mc_port = 25565
mc_version = "Nieznana" # Domyślna wartość wersji

# Tutaj dodaj ID autoryzowanych użytkowników do korzystania z komend
autoryzowani = []

# Konfiguracja Google Cloud Platform
gcp_project_id = os.getenv('gcp_project_id')
gcp_zone = os.getenv('gcp_zone')
vm_name = os.getenv('vm_name')
serviceaccount_file = "gcp.json"

# Funkcja do odczytu wersji serwera z pliku
def read_server_version():
    try:
        version_file = os.path.join(os.path.dirname(__file__), 'server_version.txt')
        if os.path.exists(version_file):
            with open(version_file, 'r') as file:
                return file.read().strip()
        return "Nieznana"
    except Exception as e:
        print(f"Błąd podczas odczytu wersji serwera: {e}")
        return "Nieznana"
    
# Funkcja do aktualizacji statusu bota
async def update_bot_status():
    try:
        server = JavaServer(mc_ip, mc_port)
        status = server.status()
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=f"{status.players.online}/{status.players.max} graczy online"
            ),
            status=discord.Status.online
        )
    except Exception as e:
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"Serwer offline"
            ),
            status=discord.Status.dnd
        )


# Zadanie cykliczne sprawdzające status serwera
@tasks.loop(minutes=1)
async def check_server_status():
    await update_bot_status()


# Event uruchamiany po zalogowaniu bota
@bot.event
async def on_ready():
    print(f'Zalogowano jako {bot.user.name}')
    print(f'ID bota: {bot.user.id}')

    # Odczytaj wersję serwera
    global mc_version
    mc_version = read_server_version()
    print(f'Wersja serwera: {mc_version}')

    # Uruchom sprawdzanie statusu serwera
    check_server_status.start()

    # Synchronizuj komendy aplikacji
    try:
        synced = await bot.tree.sync()
        print(f'Zsynchronizowano {len(synced)} komend aplikacji')
    except Exception as e:
        print(f'Błąd podczas synchronizacji komend: {e}')


# Slash komenda do sprawdzania statusu serwera Minecraft
@bot.tree.command(name='status', description='Sprawdza status serwera Minecraft')
async def status_slash(interaction: discord.Interaction):
    if interaction.user.id not in autoryzowani:
        embed = discord.Embed(title="Ssij", color=discord.Color.red())
        embed.add_field(name="Oj nie będziesz!", value="Juz lecisz.", inline=False)
        await interaction.response.send_message(embed=embed)
        return

    try:
        # Próbujemy połączyć się z serwerem Minecraft
        server = JavaServer(mc_ip, mc_port)
        status = server.status()
        # Tworzymy wiadomość z informacjami o serwerze
        embed = discord.Embed(title="Status serwera Minecraft", color=discord.Color.green())
        embed.add_field(name="Status", value="Online", inline=False)
        embed.add_field(name="Gracze", value=f"{status.players.online}/{status.players.max}", inline=True)
        embed.add_field(name="Ping", value=f"{round(status.latency)} ms", inline=True)
        embed.add_field(name="Wersja", value=mc_version, inline=True)
        # Jeśli są jacyś gracze online, wyświetlamy ich listę
        if status.players.online > 0 and status.players.sample is not None:
            player_names = [player.name for player in status.players.sample]
            embed.add_field(name="Aktywni gracze", value=", ".join(player_names), inline=False)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        # W przypadku błędu wyświetlamy informację o offline
        embed = discord.Embed(title="Status serwera Minecraft", color=discord.Color.red())
        embed.add_field(name="Status", value="Offline", inline=False)
        embed.add_field(name="Błąd", value=str(e), inline=False)
        await interaction.response.send_message(embed=embed)

# Komenda do uruchamiania maszyny wirtualnej na GCP
@bot.tree.command(name='start', description='Uruchamia maszynę wirtualną Google Cloud Platform')
async def startvm(interaction: discord.Interaction):
    if interaction.user.id not in autoryzowani:
        embed = discord.Embed(title="Ssij", color=discord.Color.red())
        embed.add_field(name="Oj nie będziesz!", value="Juz lecisz.", inline=False)
        await interaction.response.send_message(embed=embed)
        return
    try:
        embed = discord.Embed(title="Uruchamianie serwera MC", color=discord.Color.green())
        embed.add_field(name="Status", value="Trwa uruchamianie maszyny wirtualnej. Jeżeli trwa dłużej niż 3 minuty, skontaktuj się z Ropuchą lub Dziadkiem", inline=False)
        instance_client = compute_v1.InstancesClient.from_service_account_file(serviceaccount_file)
        instance_client.start(project=gcp_project_id, zone=gcp_zone, instance=vm_name)
        await interaction.response.send_message(embed=embed)

    except Exception as e:
        embed = discord.Embed(title="Błąd", color=discord.Color.red())
        embed.add_field(name="Błąd", value=str(e), inline=False)
        await interaction.response.send_message(embed=embed)

# Komenda do wylaczania maszyny wirtuanlej na GCP
@bot.tree.command(name="stop", description="Zatrzymuje maszynę wirtualną Google Cloud Platform")
async def stopvm(interaction: discord.Interaction):
    if interaction.user.id not in autoryzowani:
        embed = discord.Embed(title="Ssij", color=discord.Color.red())
        embed.add_field(name="Oj nie będziesz!", value="Juz lecisz.", inline=False)
        await interaction.response.send_message(embed=embed)
        return
    try:
        instance_client = compute_v1.InstancesClient.from_service_account_file(serviceaccount_file)
        instance_client.stop(project=gcp_project_id, zone=gcp_zone, instance=vm_name)
        embed = discord.Embed(title="Zatrzymywanie serwera MC", color=discord.Color.yellow())
        embed.add_field(name="Status", value="Trwa zatrzymywanie maszyny wirtualnej.", inline=False)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        embed = discord.Embed(title="Błąd", color=discord.Color.red())
        embed.add_field(name="Status", value=str(e), inline=False)
        await interaction.response.send_message(embed=embed)

# Uruchamiamy bota
bot.run(os.getenv('dc_mc_token'))
