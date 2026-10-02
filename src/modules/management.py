import discord
from discord.ext import commands
from src.config import get_env_var, save_env_var

class ManagementCog(commands.Cog):
    """Módulo de Gerenciamento do Servidor (Boas-Vindas e Despedida)."""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def format_template(template: str, member: discord.Member, channel: discord.TextChannel = None) -> str:
        """Substitui placeholders dinâmicos na mensagem."""
        if not template:
            return ""
        
        server = member.guild
        msg = template
        msg = msg.replace("{user.mention}", member.mention)
        msg = msg.replace("{user.name}", member.name)
        msg = msg.replace("{user}", member.mention)
        msg = msg.replace("{server}", server.name if server else "Servidor")
        msg = msg.replace("{member_count}", str(server.member_count if server else 0))
        
        if channel:
            msg = msg.replace("{channel}", channel.mention)
        else:
            msg = msg.replace("{channel}", "#canal")

        return msg

    @commands.command(name="set_welcome", aliases=["setwelcome"])
    @commands.has_permissions(administrator=True)
    async def set_welcome(self, ctx, *, args: str = None):
        """
        Configura o canal de boas-vindas.
        Uso: !set welcome to #canal
        """
        if not ctx.message.channel_mentions:
            await ctx.send("❌ **Mencione o canal de texto desejado!** Exemplo: `!set welcome to #boas-vindas`")
            return

        target_channel = ctx.message.channel_mentions[0]
        save_env_var("WELCOME_CHANNEL_ID", str(target_channel.id))
        
        await ctx.send(f"✅ **Canal de boas-vindas configurado com sucesso para:** {target_channel.mention}!")

    @commands.command(name="set_goodbye", aliases=["setgoodbye"])
    @commands.has_permissions(administrator=True)
    async def set_goodbye(self, ctx, *, args: str = None):
        """
        Configura o canal de despedida.
        Uso: !set goodbye to #canal
        """
        if not ctx.message.channel_mentions:
            await ctx.send("❌ **Mencione o canal de texto desejado!** Exemplo: `!set goodbye to #adeus`")
            return

        target_channel = ctx.message.channel_mentions[0]
        save_env_var("GOODBYE_CHANNEL_ID", str(target_channel.id))

        await ctx.send(f"👋 **Canal de despedida configurado com sucesso para:** {target_channel.mention}!")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel_id_str = get_env_var("WELCOME_CHANNEL_ID", "")
        if not channel_id_str or not channel_id_str.isdigit():
            return

        channel = member.guild.get_channel(int(channel_id_str))
        if not channel:
            return

        raw_template = get_env_var("WELCOME_MSG", "🎉 Seja muito bem-vindo(a) ao **{server}**, {user}! Agora somos {member_count} membros!")
        image_url = get_env_var("WELCOME_IMAGE_URL", "")

        formatted_msg = self.format_template(raw_template, member, channel)
        
        embed = discord.Embed(
            title=f"✨ Novo Membro no {member.guild.name}!",
            description=formatted_msg,
            color=discord.Color.brand_green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if image_url:
            embed.set_image(url=image_url)

        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"Erro ao enviar mensagem de boas-vindas: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel_id_str = get_env_var("GOODBYE_CHANNEL_ID", "")
        if not channel_id_str or not channel_id_str.isdigit():
            return

        channel = member.guild.get_channel(int(channel_id_str))
        if not channel:
            return

        raw_template = get_env_var("GOODBYE_MSG", "👋 {user.name} saiu do servidor **{server}**. Agora somos {member_count} membros.")
        image_url = get_env_var("GOODBYE_IMAGE_URL", "")

        formatted_msg = self.format_template(raw_template, member, channel)

        embed = discord.Embed(
            title=f"👋 Despedida",
            description=formatted_msg,
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if image_url:
            embed.set_image(url=image_url)

        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"Erro ao enviar mensagem de despedida: {e}")

async def setup(bot):
    await bot.add_cog(ManagementCog(bot))
