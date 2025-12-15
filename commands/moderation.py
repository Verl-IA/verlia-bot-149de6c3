import discord
from discord.ext import commands
from discord import app_commands
from database.manager import db

class Moderation(commands.Cog):
    async def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="ban", description="Bane um usuário e registra no banco de dados.")
    @app_commands.describe(user="O usuário a ser banido.", motivo="O motivo do banimento.")
    @app_commands.checks.has_permissions(ban_members=True) # Apenas quem tem permissão de banir pode usar
    async async def ban(self, interaction: discord.Interaction, user: discord.Member, motivo: str = "Sem motivo especificado."):
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
            # Bane o usuário
            await user.ban(reason=motivo)
            
            # Salva no banco de dados "bans"
            ban_data = {
                "user_id": str(user.id),
                "user_name": user.name,
                "banned_by_id": str(interaction.user.id),
                "banned_by_name": interaction.user.name,
                "reason": motivo,
                "guild_id": str(interaction.guild.id),
                "timestamp": discord.utils.utcnow().isoformat() # Registra a hora do banimento
            }
            await db.save("bans", ban_data)
            
            await interaction.response.send_message(f"🔨 {user.mention} foi banido! Motivo: **{motivo}**", ephemeral=False)
            
        except discord.Forbidden:
            await interaction.response.send_message("Eu não tenho permissão para banir este usuário. Certifique-se de que meu cargo está acima do cargo do usuário e que tenho a permissão 'Banir Membros'.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ocorreu um erro ao banir o usuário: `{e}`", ephemeral=True)

    @app_commands.command(name="unban", description="Desbane um usuário do servidor.")
    @app_commands.describe(user_id="O ID do usuário a ser desbanido.", motivo="O motivo do desbanimento.")
    @app_commands.checks.has_permissions(ban_members=True)
    async async def unban(self, interaction: discord.Interaction, user_id: str, motivo: str = "Sem motivo especificado."):
        try:
            user = discord.Object(id=int(user_id))
            await interaction.guild.unban(user, reason=motivo)
            
            await interaction.response.send_message(f"✅ O usuário com ID `{user_id}` foi desbanido! Motivo: **{motivo}**", ephemeral=False)
            
            # Opcional: Remover o registro do banco de dados ou marcá-lo como "desbanido"
            # await db.delete("bans", {"user_id": user_id, "guild_id": str(interaction.guild.id)})
            
        except discord.NotFound:
            await interaction.response.send_message("Não foi possível encontrar este ID na lista de banidos do servidor.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Eu não tenho permissão para desbanir usuários. Certifique-se de que tenho a permissão 'Banir Membros'.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("O ID do usuário fornecido é inválido. Por favor, forneça um ID numérico.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Ocorreu um erro ao desbanir o usuário: `{e}`", ephemeral=True)

    @app_commands.command(name="listarbans", description="Lista os últimos usuários banidos registrados no banco de dados.")
    @app_commands.checks.has_permissions(ban_members=True) # Apenas quem pode banir pode ver a lista
    async async def list_bans(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False) # Permite que a resposta demore um pouco

        result = await db.get("bans", {"guild_id": str(interaction.guild.id)})
        
        if not result or not result.get("data"):
            await interaction.followup.send("Nenhum banimento encontrado no registro para este servidor. 😔")
            return

        embed = discord.Embed(title="🔨 Registro de Banimentos", color=discord.Color.red())
        for ban in result["data"]:
            user_name = ban.get("user_name", "Desconhecido")
            user_id = ban.get("user_id", "ID Desconhecido")
            banned_by_name = ban.get("banned_by_name", "Desconhecido")
            reason = ban.get("reason", "Sem motivo.")
            timestamp = ban.get("timestamp", "Não informado.")

            # Formata a string de forma clara
            embed.add_field(
                name=f"🚫 {user_name} (ID: {user_id})",
                value=f"**Banido por:** {banned_by_name}\n**Motivo:** {reason}\n**Data:** {discord.utils.format_dt(discord.utils.parse_time(timestamp), 'R')}",
                inline=False
            )
        
        if not embed.fields: # Caso o filtro não retorne nada válido
            await interaction.followup.send("Nenhum banimento encontrado no registro para este servidor. 😔")
        else:
            await interaction.followup.send(embed=embed)