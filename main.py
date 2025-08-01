
import interactions
import os
import asyncio
from datetime import datetime
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot activo"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

keep_alive()

bot = interactions.Client(token=os.getenv("DISCORD_BOT_TOKEN"), intents=interactions.Intents.DEFAULT)

votos = 0
votantes = set()
servidor_activo = False
hora_inicio = None

@interactions.listen()
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")
    print(f"📊 Presente en {len(bot.guilds)} servidores")
    print("✅ Listo para recibir comandos!")

@interactions.slash_command(name="apertura", description="Envía el anuncio de apertura del servidor")
async def apertura(ctx):
    global votos, votantes, servidor_activo, hora_inicio

    if servidor_activo:
        await ctx.send("❌ El servidor ya está activo. Usa `/cerrar` para cerrarlo primero.", ephemeral=True)
        return

    votos = 0
    votantes.clear()
    hora_inicio = datetime.now()

    embed = interactions.Embed(
        title="🎮 APERTURA DEL SERVIDOR",
        description=(
            "**¡Es hora de jugar juntos!**\n\n"
            f"📊 **Votos necesarios:** 5\n"
            f"✅ **Votos actuales:** {votos}/5\n"
            f"⏰ **Iniciado:** <t:{int(hora_inicio.timestamp())}:R>\n\n"
            "**¡Haz clic en el botón para votar!**"
        ),
        color=0x00FF00,
        timestamp=datetime.now()
    )
    embed.set_footer(text="Sistema de Votación", icon_url=bot.user.avatar_url)

    content = "🔔 <@&1355756789081047214> **¡NUEVA VOTACIÓN DE APERTURA!**"

    button = interactions.Button(
        style=interactions.ButtonStyle.SUCCESS,
        label="🗳️ Votar",
        custom_id="boton_votar",
        emoji="✅"
    )

    await ctx.send(content=content, embeds=embed, components=button)

@interactions.component_callback("boton_votar")
async def boton_votar_response(ctx):
    global votos, votantes, servidor_activo

    if ctx.author.id in votantes:
        await ctx.send("❌ **Ya votaste anteriormente.** Solo se permite un voto por persona.", ephemeral=True)
        return

    votantes.add(ctx.author.id)
    votos += 1

    lista_votantes = [f"<@{user_id}>" for user_id in list(votantes)[:10]]
    if len(votantes) > 10:
        lista_votantes.append(f"... y {len(votantes) - 10} más")

    new_embed = interactions.Embed(
        title="🎮 APERTURA DEL SERVIDOR",
        description=(
            "**¡Es hora de jugar juntos!**\n\n"
            f"📊 **Votos necesarios:** 5\n"
            f"✅ **Votos actuales:** {votos}/5\n"
            f"⏰ **Iniciado:** <t:{int(hora_inicio.timestamp())}:R>\n\n"
            f"**👥 Votantes ({len(votantes)}):**\n" + ", ".join(lista_votantes) + "\n\n"
            "**¡Haz clic en el botón para votar!**"
        ),
        color=0x00FF00 if votos < 5 else 0xFF6B00,
        timestamp=datetime.now()
    )
    new_embed.set_footer(text="Sistema de Votación", icon_url=bot.user.avatar_url)

    content = "🔔 <@&1355756789081047214> **¡NUEVA VOTACIÓN DE APERTURA!**"

    button = interactions.Button(
        style=interactions.ButtonStyle.SUCCESS if votos < 5 else interactions.ButtonStyle.SECONDARY,
        label=f"🗳️ Votar ({votos}/5)" if votos < 5 else "✅ Completado",
        custom_id="boton_votar",
        emoji="✅" if votos < 5 else "🎉",
        disabled=votos >= 5
    )

    await ctx.edit_origin(content=content, embeds=new_embed, components=button)
    await ctx.send(f"✅ **¡Gracias por votar, {ctx.author.mention}!** Tu voto ha sido registrado.", ephemeral=True)

    if votos >= 5:
        servidor_activo = True

        embed_actividad = interactions.Embed(
            title="🎉 ¡SERVIDOR ACTIVADO!",
            description=(
                "**El servidor está ahora en actividad**\n\n"
                "🎮 **Servidor #1**\n"
                "🔑 **Código:** `6fc44mpz`\n\n"
                "**¡Disfruta del rol y diviértete!** ✨\n"
                f"⏰ **Activado:** <t:{int(datetime.now().timestamp())}:T>"
            ),
            color=0x00FF00
        )
        embed_actividad.set_footer(text="¡Que tengan una excelente partida!", icon_url=bot.user.avatar_url)

        await ctx.send(embeds=embed_actividad)

@interactions.slash_command(name="estado", description="Muestra el estado actual del servidor")
async def estado(ctx):
    if servidor_activo:
        embed = interactions.Embed(
            title="📊 Estado del Servidor",
            description=(
                "🟢 **Estado:** ACTIVO\n"
                "🎮 **Servidor:** #1\n"
                "🔑 **Código:** `6fc44mpz`\n"
                f"👥 **Votantes:** {len(votantes)}\n"
                f"⏰ **Activo desde:** <t:{int(hora_inicio.timestamp())}:R>"
            ),
            color=0x00FF00
        )
    else:
        embed = interactions.Embed(
            title="📊 Estado del Servidor",
            description=(
                "🔴 **Estado:** INACTIVO\n"
                "📝 **Para activar:** Usa `/apertura`\n"
                "📊 **Votos necesarios:** 5"
            ),
            color=0xFF0000
        )

    await ctx.send(embeds=embed, ephemeral=True)

@interactions.slash_command(name="cerrar", description="Cierra el servidor activo (Solo administradores)")
async def cerrar(ctx):
    global servidor_activo, votos, votantes

    if not ctx.author.guild_permissions.ADMINISTRATOR:
        await ctx.send("❌ Solo los administradores pueden cerrar el servidor.", ephemeral=True)
        return

    if not servidor_activo:
        await ctx.send("❌ No hay ningún servidor activo para cerrar.", ephemeral=True)
        return

    servidor_activo = False
    votos = 0
    votantes.clear()

    embed = interactions.Embed(
        title="🔴 Servidor Cerrado",
        description=(
            "El servidor ha sido cerrado por un administrador.\n\n"
            "**Para volver a activarlo:**\n"
            "Usa `/apertura` para iniciar una nueva votación."
        ),
        color=0xFF0000,
        timestamp=datetime.now()
    )

    await ctx.send(embeds=embed)

@interactions.slash_command(name="info", description="Información sobre el bot")
async def info(ctx):
    embed = interactions.Embed(
        title="🤖 Información del Bot",
        description=(
            "**Bot de Apertura de Servidor v2.0**\n\n"
            "**🎯 Funciones principales:**\n"
            "• `/apertura` - Inicia votación para abrir servidor\n"
            "• `/estado` - Muestra el estado actual\n"
            "• `/cerrar` - Cierra servidor (Solo admins)\n"
            "• `/info` - Muestra esta información\n\n"
            "**📊 Estadísticas:**\n"
            f"• Servidores: {len(bot.guilds)}\n"
            f"• Estado: {'🟢 Activo' if servidor_activo else '🔴 Inactivo'}\n"
            f"• Votos actuales: {votos}/5"
        ),
        color=0x0099FF,
        timestamp=datetime.now()
    )
    embed.set_footer(text="Desarrollado con ❤️", icon_url=bot.user.avatar_url)

    await ctx.send(embeds=embed, ephemeral=True)

@interactions.listen()
async def on_command_error(event):
    print(f"❌ Error en comando: {event.error}")

if __name__ == "__main__":
    print("🚀 Iniciando servidor web...")
    keep_alive()
    print("🚀 Iniciando bot...")
    bot.start()
