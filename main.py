import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import yt_dlp
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)
queue = []

load_dotenv()

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.command()
async def play(ctx, *, query: str):
    if ctx.author.voice is None:
        await ctx.send("Você precisa estar em um canal de voz.")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await voice_channel.connect()
    elif ctx.voice_client.channel != voice_channel:
        await ctx.voice_client.move_to(voice_channel)

    voice_client = ctx.voice_client

    # Adiciona à fila
    queue.append((query, ctx))
    await ctx.send(f"🎶 Música adicionada à fila: `{query}`. Posição: {len(queue)}")

    # Se não estiver tocando nada, comece a tocar
    if not voice_client.is_playing() and not voice_client.is_paused():
        await next(ctx)

async def next(ctx):
    if len(queue) == 0:
        await ctx.voice_client.disconnect()
        return

    query, ctx = queue[0]

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'quiet': True,
    }
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        resultado = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if resultado and 'entries' in resultado and resultado['entries']:
            info = resultado['entries'][0]
            audio_url = info['url']
            raw_audio = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
            source = discord.PCMVolumeTransformer(raw_audio, volume=0.5)

            def after_play(err):
                if err:
                    print("Erro na reprodução:", err)
                queue.pop(0)
                asyncio.run_coroutine_threadsafe(next(ctx), bot.loop)

            ctx.voice_client.play(source, after=after_play)
            await ctx.send(f"▶️ Tocando agora: **{info['title']}**")
        

@bot.command()
async def pause(ctx):
    voice_client = ctx.voice_client

    if not voice_client or not voice_client.is_connected():
        await ctx.send("Não estou conectado a um canal de voz.")
        return

    if voice_client.is_playing():
        voice_client.pause()
        await ctx.send("⏸️ Música pausada.")
    else:
        if not voice_client or not voice_client.is_connected():
            await  ctx.send("Não estou conectado a um canal de voz.")
            return

        if voice_client.is_paused():
            voice_client.resume()
            await ctx.send("▶️ Música retomada.")
        else:
            await ctx.send("A música não está pausada.")

@bot.command()
async def stop(ctx):
    voice_client = ctx.voice_client

    if not voice_client or not voice_client.is_connected():
        await ctx.send("Não estou conectado a um canal de voz.")
        return

    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    queue.clear()
    await voice_client.disconnect()

@bot.command()
async def skip(ctx):
    voice_client = ctx.voice_client

    if not voice_client or not voice_client.is_connected():
        await ctx.send("❌ Não estou em um canal de voz.")
        return

    if not voice_client.is_playing():
        await ctx.send("⚠️ Nenhuma música está tocando no momento.")
        return

    voice_client.stop()
    await ctx.send("⏭️ Próxima música!")

# Substitua pelo seu token
bot.run(os.getenv("DISCORD_TOKEN"))

