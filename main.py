import discord
import logging
import os
from discord.ext import commands

"""Bot Discord - Criado com Verl.ia"""

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
log = logging.getLogger('bot')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

class Bot(commands.Bot):
    """Classe Bot."""
    def __init__(self):
        super().__init__(command_prefix='!', intents=intents, help_command=None)
    
    async def setup_hook(self):
        # Carregando as cogs
        cogs = ['commands.economy', 'commands.moderation', 'commands.utility'] # Adicionado 'commands.economy'
        for cog in cogs:
            try:
                await self.load_extension(cog)
                log.info(f'✅ {cog} carregado')
            except Exception as e:
                log.error(f'❌ Erro em {cog}: {e}')
    
    async def on_ready(self):
        log.info(f'🤖 {self.user} online!')
        try:
            await self.tree.sync()
            log.info('✅ Slash commands sincronizados')
        except Exception as e:
            log.error(f'❌ Erro sync: {e}')

bot = Bot()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Você não tem permissão para usar este comando!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'❌ Ops! Você esqueceu de algo. Faltou o argumento: `{error.param.name}`')
    elif isinstance(error, commands.CommandOnCooldown):
        seconds = int(error.retry_after)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        await ctx.send(f"⏳ Este comando está em cooldown para você! Tente novamente em {'%dh %dm %ds' % (hours, minutes, seconds)}.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Não consegui encontrar esse membro no servidor.")
    else:
        log.error(f"❌ Erro global de comando em {ctx.command}: {error}")
        await ctx.send(f"❌ Ocorreu um erro inesperado: {error}") # Mensagem genérica para outros erros

if __name__ == '__main__':
    token = os.environ.get('BOT_TOKEN')
    if not token:
        log.error('❌ BOT_TOKEN não configurado! Certifique-se de definir a variável de ambiente.')
    else:
        bot.run(token)