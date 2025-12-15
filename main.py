import discord
from discord.ext import commands
import os

# Importa os comandos de moderação
from commands.moderation import Moderation
from database.manager import VerliaDB

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Necessário para eventos de membro como ban
intents.bans = True # Necessário para eventos de ban

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async async def on_ready():
    print(f'✅ Bot conectado como {bot.user}')
    print(f'📊 Servidores: {len(bot.guilds)}')
    await bot.add_cog(Moderation(bot)) # Adiciona a cog de moderação
    await bot.tree.sync()  # Sincroniza slash commands
    print("Comandos sincronizados e cogs carregadas.")

# ═══════════════════════════════════════════
# 🔌 CONEXÃO DO BOT - NUNCA REMOVA ESTA LINHA
# ═══════════════════════════════════════════
bot.run(os.environ.get('BOT_TOKEN'))