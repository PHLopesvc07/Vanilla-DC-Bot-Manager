import time
import random
import discord
from discord.ext import commands
from src.database import get_db_connection

class EconomyCog(commands.Cog):
    """Módulo de Economia e Sistema de Níveis com SQLite Local."""

    def __init__(self, bot):
        self.bot = bot

    def get_user(self, user_id: int) -> dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_economy WHERE user_id=?", (user_id,))
        row = cursor.fetchone()

        if not row:
            cursor.execute("""
                INSERT INTO user_economy (user_id, balance, xp, level, last_msg_time, last_daily)
                VALUES (?, 100, 0, 1, 0, 0)
            """, (user_id,))
            conn.commit()
            cursor.execute("SELECT * FROM user_economy WHERE user_id=?", (user_id,))
            row = cursor.fetchone()

        data = dict(row)
        conn.close()
        return data

    def update_user(self, user_id: int, **kwargs):
        conn = get_db_connection()
        cursor = conn.cursor()
        set_clause = ", ".join([f"{k}=?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        cursor.execute(f"UPDATE user_economy SET {set_clause} WHERE user_id=?", values)
        conn.commit()
        conn.close()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        now = time.time()
        user = self.get_user(message.author.id)

        # Cooldown de 60 segundos para XP
        if now - user["last_msg_time"] > 60:
            new_xp = user["xp"] + random.randint(15, 25)
            new_level = (new_xp // 100) + 1
            new_bal = user["balance"]

            if new_level > user["level"]:
                reward = new_level * 50
                new_bal += reward
                try:
                    await message.channel.send(
                        f"🎉 **Parabéns {message.author.mention}!** Você subiu para o **Nível {new_level}** e ganhou **{reward} moedas**!"
                    )
                except Exception:
                    pass

            self.update_user(message.author.id, xp=new_xp, level=new_level, balance=new_bal, last_msg_time=now)

    @commands.command(name="profile", aliases=["perfil", "level", "xp", "bal", "saldo"])
    async def profile_cmd(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user = self.get_user(target.id)

        embed = discord.Embed(
            title=f"💳 Perfil de {target.display_name}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="⭐ Nível", value=str(user["level"]), inline=True)
        embed.add_field(name="✨ XP Total", value=f"{user['xp']} XP", inline=True)
        embed.add_field(name="💰 Saldo", value=f"{user['balance']} Moedas", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily_cmd(self, ctx):
        user = self.get_user(ctx.author.id)
        now = time.time()
        cooldown = 86400  # 24 horas

        if now - user["last_daily"] < cooldown:
            remaining = int(cooldown - (now - user["last_daily"]))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await ctx.send(f"⏳ **Você já resgatou seu Daily hoje!** Tente novamente em `{hours}h {minutes}m`.")
            return

        reward = random.randint(150, 300)
        new_bal = user["balance"] + reward
        self.update_user(ctx.author.id, balance=new_bal, last_daily=now)
        await ctx.send(f"🎁 **Você resgatou seu prêmio Daily de {reward} moedas!** Saldo atual: {new_bal} moedas.")

    @commands.command(name="pay", aliases=["pagar", "transferir"])
    async def pay_cmd(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            await ctx.send("❌ Informe um valor positivo de moedas!")
            return

        if member.id == ctx.author.id:
            await ctx.send("❌ Você não pode transferir moedas para si mesmo!")
            return

        sender = self.get_user(ctx.author.id)
        receiver = self.get_user(member.id)

        if sender["balance"] < amount:
            await ctx.send(f"❌ **Saldo insuficiente!** Você possui apenas {sender['balance']} moedas.")
            return

        self.update_user(ctx.author.id, balance=sender["balance"] - amount)
        self.update_user(member.id, balance=receiver["balance"] + amount)
        await ctx.send(f"💸 {ctx.author.mention} transferiu **{amount} moedas** para {member.mention}!")

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
