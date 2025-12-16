import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
from utils.database import db

class Economy(commands.Cog):
    """Classe Economy."""
    def __init__(self, bot):
        self.bot = bot

    async def get_user_economy(self, user_id, guild_id):
        """Retorna os dados de economia de um usuário ou cria se não existir."""
        user_data = await db.find_one("economy", {"user_id": str(user_id), "guild_id": str(guild_id)})
        if not user_data:
            user_data = {
                "user_id": str(user_id),
                "guild_id": str(guild_id),
                "wallet": 0,
                "bank": 0,
                "last_daily": None,
                "last_work": None,
                "cooldown_rob": None
            }
            await db.insert("economy", user_data)
        return user_data

    @commands.hybrid_command(name="balance", description="Verifica seu saldo.")
    async def balance(self, ctx: commands.Context):
        user_data = await self.get_user_economy(ctx.author.id, ctx.guild.id)
        
        embed = discord.Embed(
            title="💰 Seu Saldo",
            description=f"**Carteira:** {user_data['wallet']:,} 🪙\n**Banco:** {user_data['bank']:,} 🪙\n**Total:** {(user_data['wallet'] + user_data['bank']):,} 🪙",
            color=discord.Color.gold()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="daily", description="Colete sua recompensa diária!")
    @commands.cooldown(1, 86400, commands.BucketType.user) # 24 horas (86400 segundos)
    async def daily(self, ctx: commands.Context):
        user_data = await self.get_user_economy(ctx.author.id, ctx.guild.id)
        
        last_daily_str = user_data["last_daily"]
        if last_daily_str:
            last_daily = datetime.fromisoformat(last_daily_str)
            if datetime.utcnow() < last_daily + timedelta(days=1):
                # Calcular tempo restante para o usuário
                next_daily_time = last_daily + timedelta(days=1)
                time_diff = next_daily_time - datetime.utcnow()
                hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                await ctx.send(f"⏰ Você já coletou sua recompensa diária! Tente novamente em {hours}h {minutes}m.")
                self.daily.reset_cooldown(ctx) # Resetar o cooldown se for muito cedo
                return
        
        reward = random.randint(500, 1500)
        user_data["wallet"] += reward
        user_data["last_daily"] = datetime.utcnow().isoformat()
        
        await db.update("economy", 
                        {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id)},
                        {"wallet": user_data["wallet"], "last_daily": user_data["last_daily"]})
        
        embed = discord.Embed(
            title="🎁 Recompensa Diária Coletada!",
            description=f"Você recebeu **{reward:,} 🪙** na sua carteira!",
            color=discord.Color.green()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="work", description="Trabalhe para ganhar dinheiro!")
    @commands.cooldown(1, 3600, commands.BucketType.user) # 1 hora
    async def work(self, ctx: commands.Context):
        user_data = await self.get_user_economy(ctx.author.id, ctx.guild.id)

        last_work_str = user_data["last_work"]
        if last_work_str:
            last_work = datetime.fromisoformat(last_work_str)
            if datetime.utcnow() < last_work + timedelta(hours=1):
                next_work_time = last_work + timedelta(hours=1)
                time_diff = next_work_time - datetime.utcnow()
                minutes, seconds = divmod(int(time_diff.total_seconds()), 60)
                await ctx.send(f"⏰ Você já trabalhou recentemente! Tente novamente em {minutes}m {seconds}s.")
                self.work.reset_cooldown(ctx)
                return

        rewards = {
            "Programador": random.randint(150, 400),
            "Gamer Profissional": random.randint(100, 300),
            "Designer de Emojis": random.randint(120, 350),
            "Caçador de Bugs": random.randint(200, 500),
            "Testador de Bots": random.randint(180, 450)
        }
        
        job = random.choice(list(rewards.keys()))
        amount = rewards[job]
        
        user_data["wallet"] += amount
        user_data["last_work"] = datetime.utcnow().isoformat()

        await db.update("economy",
                        {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id)},
                        {"wallet": user_data["wallet"], "last_work": user_data["last_work"]})
        
        embed = discord.Embed(
            title=f"💼 Você trabalhou como {job}!",
            description=f"Você ganhou **{amount:,} 🪙** na sua carteira!",
            color=discord.Color.blue()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="deposit", description="Deposita dinheiro da sua carteira para o banco.")
    async def deposit(self, ctx: commands.Context, amount: int):
        if amount <= 0:
            return await ctx.send("Você precisa depositar um valor positivo!")

        user_data = await self.get_user_economy(ctx.author.id, ctx.guild.id)

        if user_data["wallet"] < amount:
            return await ctx.send(f"Você não tem **{amount:,} 🪙** na sua carteira para depositar.")
        
        user_data["wallet"] -= amount
        user_data["bank"] += amount

        await db.update("economy",
                        {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id)},
                        {"wallet": user_data["wallet"], "bank": user_data["bank"]})
        
        embed = discord.Embed(
            title="🏦 Depósito Realizado",
            description=f"Você depositou **{amount:,} 🪙** no seu banco.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Carteira Atual", value=f"{user_data['wallet']:,} 🪙")
        embed.add_field(name="Banco Atual", value=f"{user_data['bank']:,} 🪙")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="withdraw", description="Retira dinheiro do seu banco para a carteira.")
    async def withdraw(self, ctx: commands.Context, amount: int):
        if amount <= 0:
            return await ctx.send("Você precisa retirar um valor positivo!")

        user_data = await self.get_user_economy(ctx.author.id, ctx.guild.id)

        if user_data["bank"] < amount:
            return await ctx.send(f"Você não tem **{amount:,} 🪙** no seu banco para retirar.")
        
        user_data["bank"] -= amount
        user_data["wallet"] += amount

        await db.update("economy",
                        {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id)},
                        {"wallet": user_data["wallet"], "bank": user_data["bank"]})
        
        embed = discord.Embed(
            title="💸 Retirada Realizada",
            description=f"Você retirou **{amount:,} 🪙** do seu banco.",
            color=discord.Color.red()
        )
        embed.add_field(name="Carteira Atual", value=f"{user_data['wallet']:,} 🪙")
        embed.add_field(name="Banco Atual", value=f"{user_data['bank']:,} 🪙")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="pay", description="Transfere dinheiro para outro usuário.")
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send("Você precisa enviar um valor positivo!")
        if member.bot:
            return await ctx.send("Você não pode pagar bots!")
        if member.id == ctx.author.id:
            return await ctx.send("Você não pode pagar a si mesmo!")

        sender_data = await self.get_user_economy(ctx.author.id, ctx.guild.id)
        receiver_data = await self.get_user_economy(member.id, ctx.guild.id)

        if sender_data["wallet"] < amount:
            return await ctx.send(f"Você não tem **{amount:,} 🪙** na sua carteira para enviar.")

        sender_data["wallet"] -= amount
        receiver_data["wallet"] += amount

        await db.update("economy",
                        {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id)},
                        {"wallet": sender_data["wallet"]})
        await db.update("economy",
                        {"user_id": str(member.id), "guild_id": str(ctx.guild.id)},
                        {"wallet": receiver_data["wallet"]})
        
        embed = discord.Embed(
            title="🤝 Transferência Realizada",
            description=f"Você enviou **{amount:,} 🪙** para **{member.display_name}**.",
            color=discord.Color.green()
        )
        embed.add_field(name="Sua Carteira", value=f"{sender_data['wallet']:,} 🪙")
        embed.add_field(name="Carteira de {member.display_name}", value=f"{receiver_data['wallet']:,} 🪙")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="rob", description="Tente roubar dinheiro de outro usuário. Cuidado!")
    @commands.cooldown(1, 10800, commands.BucketType.user) # 3 horas de cooldown
    async def rob(self, ctx: commands.Context, member: discord.Member):
        if member.bot:
            await ctx.send("Você não pode roubar bots, eles não têm carteira!")
            self.rob.reset_cooldown(ctx)
            return
        if member.id == ctx.author.id:
            await ctx.send("Você não pode roubar a si mesmo, seria autodestrutivo!")
            self.rob.reset_cooldown(ctx)
            return
        
        if member.status == discord.Status.offline:
            await ctx.send("Não é possível roubar usuários offline. Eles estão escondendo seus bens!")
            self.rob.reset_cooldown(ctx)
            return

        robber_data = await self.get_user_economy(ctx.author.id, ctx.guild.id)
        victim_data = await self.get_user_economy(member.id, ctx.guild.id)

        # Cooldown para roubo
        cooldown_rob_str = robber_data["cooldown_rob"]
        if cooldown_rob_str:
            cooldown_rob = datetime.fromisoformat(cooldown_rob_str)
            if datetime.utcnow() < cooldown_rob + timedelta(hours=3):
                next_rob_time = cooldown_rob + timedelta(hours=3)
                time_diff = next_rob_time - datetime.utcnow()
                hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                await ctx.send(f"🚓 Você precisa esperar para tentar outro roubo! Tente novamente em {hours}h {minutes}m {seconds}s.")
                return # Não resetar cooldown da cog se for cooldown do DB

        if victim_data["wallet"] < 500: # Não roubar se a vítima tiver pouco dinheiro
            await ctx.send(f"🕵️ {member.display_name} tem muito pouco dinheiro na carteira (<500 🪙). Não vale a pena o risco!")
            return

        success_chance = random.randint(1, 100)
        
        # Obter ou criar dados para o leaderboard_stats antes de atualizar
        robber_stats = await db.find_one("leaderboard_stats", {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id)})
        if not robber_stats:
            await db.insert("leaderboard_stats", {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id), "total_money": 0, "items_owned": 0, "rob_success": 0, "rob_fails": 0})
            robber_stats = await db.find_one("leaderboard_stats", {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id)}) # Fetch again after insertion

        if success_chance <= 60: # 60% de chance de sucesso
            amount_robbed = random.randint(int(victim_data["wallet"] * 0.1), int(victim_data["wallet"] * 0.4)) # Rouba entre 10% e 40%
            
            robber_data["wallet"] += amount_robbed
            victim_data["wallet"] -= amount_robbed
            robber_data["cooldown_rob"] = datetime.utcnow().isoformat()

            await db.update("economy",
                            {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id)},
                            {"wallet": robber_data["wallet"], "cooldown_rob": robber_data["cooldown_rob"]})
            await db.update("economy",
                            {"user_id": str(member.id), "guild_id": str(ctx.guild.id)},
                            {"wallet": victim_data["wallet"]})
            
            # Atualizar rob_success no leaderboard_stats
            await db.update("leaderboard_stats",
                            {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id)},
                            {"rob_success": robber_stats["rob_success"] + 1})


            embed = discord.Embed(
                title="✅ Roubo Bem Sucedido!",
                description=f"Você conseguiu roubar **{amount_robbed:,} 🪙** de {member.display_name}!",
                color=discord.Color.green()
            )
            embed.add_field(name="Sua Carteira", value=f"{robber_data['wallet']:,} 🪙")
            embed.add_field(name="Carteira de {member.display_name}", value=f"{victim_data['wallet']:,} 🪙")
            await ctx.send(embed=embed)
        else: # Falha
            fine_amount = random.randint(int(robber_data["wallet"] * 0.05), int(robber_data["wallet"] * 0.2)) # Multa entre 5% e 20%
            if fine_amount > robber_data["wallet"]: # Não deixar o usuário ficar com saldo negativo na carteira por multa
                fine_amount = robber_data["wallet"]
            
            robber_data["wallet"] -= fine_amount
            robber_data["cooldown_rob"] = datetime.utcnow().isoformat()

            await db.update("economy",
                            {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id)},
                            {"wallet": robber_data["wallet"], "cooldown_rob": robber_data["cooldown_rob"]})
            
            # Atualizar rob_fails no leaderboard_stats
            await db.update("leaderboard_stats",
                            {"user_id": str(ctx.author.id), "guild_id": str(ctx.guild.id)},
                            {"rob_fails": robber_stats["rob_fails"] + 1})
            
            embed = discord.Embed(
                title="❌ Roubo Fracassado!",
                description=f"Você foi pego tentando roubar {member.display_name} e foi multado em **{fine_amount:,} 🪙**!",
                color=discord.Color.red()
            )
            embed.add_field(name="Sua Carteira", value=f"{robber_data['wallet']:,} 🪙")
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))