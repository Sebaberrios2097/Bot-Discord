import discord
from discord.ext import commands
import datetime
import pytz
import urllib.parse, urllib.request, re
from pytube import YouTube
import asyncio
import sqlite3
import config

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='>', intents=intents)

# Crear una conexión con la base de datos
conn = sqlite3.connect('bot_sebatory.db')  
c = conn.cursor()  

# Crear la tabla 'Aweonez' si no existe
c.execute('''
    CREATE TABLE IF NOT EXISTS Aweonez
    (UserID INT PRIMARY KEY NOT NULL,
    Count INT NOT NULL);
''')

# Sumar barbaridad al individuo
@bot.command(name='aweonez')
async def aweonez(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send('Debes mencionar a un usuario!')
        return
    c.execute("INSERT OR REPLACE INTO Aweonez (UserID, Count) VALUES (?, COALESCE((SELECT Count FROM Aweonez WHERE UserID = ?), 0) + 1)", (member.id, member.id))
    conn.commit()
    await ctx.send(f'{member.name} ahora tiene {c.execute("SELECT Count FROM Aweonez WHERE UserID = ?", (member.id,)).fetchone()[0]} aweonez.')

# Conteo de barbaridades
@bot.command(name='aweonometro')
async def aweonometro(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send('Debes mencionar a un usuario!')
        return
    count = c.execute("SELECT Count FROM Aweonez WHERE UserID = ?", (member.id,)).fetchone()
    if count is None:
        await ctx.send(f'{member.name} no tiene aweonez.')
    else:
        await ctx.send(f'{member.name} tiene {count[0]} aweonez.')

# Buscar en youtube
@bot.command(name='youtube')
async def youtube(ctx, *, search):
    query_string = urllib.parse.urlencode({
        'search_query': search
    })
    html_content = urllib.request.urlopen(
        'http://www.youtube.com/results?' + query_string
    )
    search_results = re.findall(
        r"watch\?v=(\S{11})", html_content.read().decode()
    )
    await ctx.send('https://www.youtube.com/watch?v=' + search_results[0])

@bot.command()
async def conectar(ctx):
    # Comprueba si el autor del mensaje está conectado a un canal de voz
    if ctx.author.voice is None:
        await ctx.send("Debes estar en un canal de voz para usar este comando.")
        return

    # Comprueba si el bot ya está conectado a un canal de voz
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()

    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.send(f'Conectado al canal de voz: {channel}')

@bot.command()
async def desconectar(ctx):
    # Comprueba si el bot está conectado a un canal de voz
    if ctx.voice_client is None:
        await ctx.send("No estoy conectado a un canal de voz.")
        return

    await ctx.voice_client.disconnect()
    await ctx.send('Desconectado del canal de voz.')

@bot.command()
async def play(ctx, *, url):
    # Comprueba si el autor del mensaje está conectado a un canal de voz
    if ctx.author.voice is None:
        await ctx.send("Debes estar en un canal de voz para usar este comando.")
        return

    # Comprueba si el bot ya está conectado a un canal de voz
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()

    # Conecta al canal de voz del autor del mensaje
    channel = ctx.author.voice.channel
    await channel.connect()

    # Descarga la música de YouTube utilizando pytube
    try:
        youtube = YouTube(url)
        stream = youtube.streams.get_audio_only()
        url2 = stream.url
    except Exception as e:
        await ctx.send(f"Ocurrió un error al obtener el audio de YouTube: {str(e)}")
        return

    # Reproduce la música
    ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(executable="C:/ffmpeg/bin/ffmpeg.exe", source=url2, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")), after=lambda e: print(f"Error: {e}") if e else None)
    await ctx.send(f"Reproduciendo: {url}")
    

@bot.command()
async def stop(ctx):
    # Comprueba si el bot está conectado a un canal de voz
    if ctx.voice_client is None:
        await ctx.send("No estoy conectado a un canal de voz.")
        return

    # Detiene la reproducción y desconecta del canal de voz
    ctx.voice_client.stop()
    await ctx.voice_client.disconnect()

# Infor del servidor
@bot.command()
async def info(ctx):
    try:
        owner = await bot.fetch_user(ctx.guild.owner_id)

        # Define la zona horaria de Chile
        chile_tz = pytz.timezone('Chile/Continental')
        
        # Obtiene la fecha y hora actual en la zona horaria de Chile
        now_in_chile = datetime.datetime.now(chile_tz)

        embed = discord.Embed(title="Bot de prueba", description="Bot para contar las barbaridades explayadas por ciertos individuos", color=0xeee657, timestamp=now_in_chile)
        embed.add_field(name= "Servidor creado el ", value=f"{ctx.guild.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        embed.add_field(name= "Dueño del servidor", value=f"{owner.name}")
        embed.add_field(name= "ID del servidor", value=f"{ctx.guild.id}")
        embed.add_field(name= "Miembros", value=f"{ctx.guild.member_count}")
        embed.add_field(name= "Miembros conectados", value=f"{len([m for m in ctx.guild.members if m.status != discord.Status.offline])}")
        embed.add_field(name= "Miembros desconectados", value=f"{len([m for m in ctx.guild.members if m.status == discord.Status.offline])}")
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        await ctx.send(f"Ocurrió un error: {e}")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name='>help'))
    print('¡Estoy listo!')

@bot.command()
async def ping(ctx):
    await ctx.send('pong')



bot.run(config.TOKEN)