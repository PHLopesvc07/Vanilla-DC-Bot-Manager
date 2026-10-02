import discord
from discord.ext import commands

class UserUtilsCog(commands.Cog):
    """Módulo USER: Gerenciamento de Cores, Cargos e Promoções."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setcolor", aliases=["cor"])
    async def set_color(self, ctx, color_hex: str):
        """Define a cor do cargo do usuário (requer permissão de Gerenciar Cargos)."""
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send("❌ **O bot precisa da permissão 'Gerenciar Cargos' para alterar cores!**")
            return

        clean_hex = color_hex.lstrip('#')
        try:
            color_int = int(clean_hex, 16)
        except ValueError:
            await ctx.send("❌ **Código Hex de cor inválido!** Use formatos como `#FF0000` ou `00FF00`.")
            return

        role_name = f"Cor_{ctx.author.name}"
        existing_role = discord.utils.get(ctx.guild.roles, name=role_name)

        try:
            if existing_role:
                await existing_role.edit(color=discord.Color(color_int))
            else:
                existing_role = await ctx.guild.create_role(name=role_name, color=discord.Color(color_int))
                await ctx.author.add_roles(existing_role)

            await ctx.send(f"🎨 **Cor de apelido atualizada com sucesso para #{clean_hex.upper()}!**")
        except Exception as e:
            await ctx.send(f"❌ Erro ao atualizar cor de cargo: {e}")

    @commands.command(name="promover", aliases=["promote"])
    @commands.has_permissions(manage_roles=True)
    async def promote_user(self, ctx, member: discord.Member, role: discord.Role):
        """Promove um membro atribuindo um cargo. Uso: !promover @Membro @Cargo"""
        try:
            await member.add_roles(role)
            await ctx.send(f"🎖️ {member.mention} foi promovido(a) e recebeu o cargo **{role.name}**!")
        except Exception as e:
            await ctx.send(f"❌ Erro ao atribuir cargo: {e}")

async def setup(bot):
    await bot.add_cog(UserUtilsCog(bot))
