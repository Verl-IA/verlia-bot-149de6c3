import discord
from discord.ext import commands
from discord import app_commands
from database.manager import db

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="ban", description="Bane um usuário e registra no banco de dados.")
    @app_commands.describe(user="O usuário a ser banido.", motivo="O motivo do banimento.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, motivo: str = "Sem motivo especificado."):
        if user.id == interaction.user.id:
            await interaction.response.send_message("Você não pode banir a si mesmo!", ephemeral=True)
            return
        if user.bot:
            await interaction.response.send_message("Não é possível banir bots com este comando.", ephemeral=True)
            return
        if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(f"Você não pode banir {user.display_name} pois ele tem um cargo igual ou superior ao seu.", ephemeral=True)
            return

        try:
            await user.ban(reason=motivo)
            
            ban_data = {
                "user_id": str(user.id),
                "user_name": user.name,
                "banned_by_id": str(interaction.user.id),
                "banned_by_name": interaction.user.name,
                "reason": motivo,
                "guild_id": str(interaction.guild.id),
                "timestamp": discord.utils.utcnow().isoformat()
            }
            await db.save("bans", ban_data)
            
            await interaction.response.send_message(f"🔨 {user.mention} foi banido! Motivo: **{motivo}**", ephemeral=False)
            
        except discord.Forbidden:
            await interaction.response.send_message("Eu não tenho permissão para banir este usuário.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ocorreu um erro ao banir o usuário: `{e}`", ephemeral=True)

    @app_commands.command(name="unban", description="Desbane um usuário do servidor.")
    @app_commands.describe(user_id="O ID do usuário a ser desbanido.", motivo="O motivo do desbanimento.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, motivo: str = "Sem motivo especificado."):
        try:
            user = discord.Object(id=int(user_id))
            await interaction.guild.unban(user, reason=motivo)
            
            await interaction.response.send_message(f"✅ O usuário com ID `{user_id}` foi desbanido! Motivo: **{motivo}**", ephemeral=False)
            
        except discord.NotFound:
            await interaction.response.send_message("Não foi possível encontrar este ID na lista de banidos.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Eu não tenho permissão para desbanir usuários.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("ID de usuário inválido.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ocorreu um erro: `{e}`", ephemeral=True)

    @app_commands.command(name="kick", description="Expulsa um usuário do servidor.")
    @app_commands.describe(user="O usuário a ser expulso.", motivo="O motivo da expulsão.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, motivo: str = "Sem motivo especificado."):
        if user.id == interaction.user.id:
            await interaction.response.send_message("Você não pode expulsar a si mesmo!", ephemeral=True)
            return
        if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message(f"Você não pode expulsar {user.display_name}.", ephemeral=True)
            return

        try:
            await user.kick(reason=motivo)
            await interaction.response.send_message(f"👢 {user.mention} foi expulso! Motivo: **{motivo}**", ephemeral=False)
        except discord.Forbidden:
            await interaction.response.send_message("Eu não tenho permissão para expulsar este usuário.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ocorreu um erro: `{e}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))