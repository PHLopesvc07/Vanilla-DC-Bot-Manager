import random
import aiohttp
import discord
from discord.ext import commands

# Lista de categorias / tags pré-configuradas populares
# Dicionário de tags comuns e organizadas por categoria nas APIs NSFW (Rule34 e Redgifs)
COMMON_NSFW_TAGS = {
    "Categorias & Estilos": [
        "femboy", "trans", "yaoi", "yuri", "hentai", "anime", 
        "real", "cosplay", "straight", "solo", "3d", "furry"
    ],
    "Filtros de Mídia": [
        "gif", "video", "animated", "sound", "mp4"
    ],
    "Exemplos de Personagens Popularmente Buscados": [
        "hatsune_miku", "2b", "tifa_lockhart", "ahri", "d.va", 
        "genshin_impact", "overwatch", "league_of_legends", "pokemon", "naruto"
    ]
}

class NSFWCog(commands.Cog):
    """Módulo NSFW com suporte avançado a tags personalizadas (personagens, animes, jogos) e filtros de mídia (Rule34 & Redgifs)."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_before_invoke(self, ctx):
        """Verifica obrigatoriamente se o canal possui a flag NSFW ativada."""
        if not getattr(ctx.channel, "is_nsfw", lambda: False)():
            await ctx.send("🔞 **Este comando só pode ser utilizado em canais de texto marcados como NSFW!**")
            raise commands.CommandError("Canal não é NSFW")

    @commands.command(name="nsfw_tags", aliases=["nsfwtags", "tags_nsfw"])
    async def nsfw_tags_cmd(self, ctx):
        """Exibe a lista de tags comuns, categorias e dicas para buscar personagens ou animes."""
        embed = discord.Embed(
            title="🔞 Tags Comuns e Dicas de Busca NSFW",
            description=(
                "Você pode buscar **qualquer tag personalizada**, **personagem**, **anime** ou **jogo** no comando `!r34`!\n"
                "Para nomes compostos ou com espaços, o bot converte os espaços em underline `_` automaticamente.\n"
            ),
            color=discord.Color.magenta()
        )

        for cat, tags in COMMON_NSFW_TAGS.items():
            embed.add_field(
                name=f"📌 {cat}",
                value=", ".join([f"`{t}`" for t in tags]),
                inline=False
            )

        embed.add_field(
            name="💬 Exemplos de Busca Personalizada:",
            value=(
                "• `!r34 2b` ➔ Personagem 2B (Nier Automata)\n"
                "• `!r34 hatsune miku video` ➔ Vídeos/GIFs da Hatsune Miku\n"
                "• `!r34 genshin impact femboy` ➔ Combinação de jogo + tag\n"
                "• `!r34 tifa lockhart gif` ➔ GIFs da Tifa Lockhart\n"
                "• `!redgifs femboy` ➔ Categoria Femboy no Redgifs\n"
            ),
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="r34", aliases=["rule34"])
    async def r34_cmd(self, ctx, *, tags: str = "all"):
        """
        Busca mídias na Rule34 por tags personalizadas (personagens, animes, jogos, estilos ou gif/video).
        Uso: !r34 [tag1 tag2...] (Ex: !r34 2b video, !r34 hatsune miku)
        """
        raw_input = tags.strip().lower()

        # Separa palavras/tags e converte espaços de termos/personagens para underline (_)
        # Tratamento para preservar palavras-chave de filtro de mídia como gif/video
        tokens = raw_input.split()
        media_filter = None
        cleaned_tokens = []

        for token in tokens:
            if token in ["gif", "video", "mp4", "animated"]:
                media_filter = token
                cleaned_tokens.append(token)
            else:
                cleaned_tokens.append(token)

        query_tags = "_".join(cleaned_tokens)
        url = f"https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&limit=50&tags={query_tags}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                        except Exception:
                            data = []

                        if not data:
                            # Tenta fallback formatando espaços por underline individuais
                            fallback_tags = raw_input.replace(" ", "_")
                            url_fallback = f"https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&limit=50&tags={fallback_tags}"
                            async with session.get(url_fallback) as resp2:
                                if resp2.status == 200:
                                    try:
                                        data = await resp2.json()
                                    except Exception:
                                        data = []

                        if not data:
                            await ctx.send(f"🔍 Nenhum resultado encontrado para a busca: `{tags}`")
                            return

                        # Filtra tipo de mídia se solicitado (gif / video)
                        if media_filter == "gif":
                            filtered = [item for item in data if item.get("file_url", "").endswith(".gif")]
                            if filtered:
                                data = filtered
                        elif media_filter in ["video", "mp4", "animated"]:
                            filtered = [item for item in data if item.get("file_url", "").endswith(('.mp4', '.webm'))]
                            if filtered:
                                data = filtered

                        item = random.choice(data)
                        file_url = item.get("file_url")

                        embed = discord.Embed(
                            title=f"🔞 Rule34: {tags.title()}",
                            description=f"🏷️ Busca: `{tags}` | 📊 Score: {item.get('score', 0)}",
                            color=discord.Color.magenta()
                        )
                        
                        if file_url.endswith(('.mp4', '.webm')):
                            await ctx.send(embed=embed)
                            await ctx.send(file_url)
                        else:
                            embed.set_image(url=file_url)
                            await ctx.send(embed=embed)
                    else:
                        await ctx.send("⚠️ Erro ao consultar a API da Rule34.")
        except Exception as e:
            await ctx.send(f"❌ Erro ao processar requisição NSFW: {e}")

    @commands.command(name="redgifs", aliases=["redgif"])
    async def redgifs_cmd(self, ctx, *, tags: str = "femboy"):
        """
        Busca GIFs/Vídeos na Redgifs por categoria/tag ou termo de busca.
        Uso: !redgifs [categoria/tag/termo]
        """
        search_query = tags.strip().replace(" ", "-")
        url = f"https://api.redgifs.com/v2/gifs/search?search_text={search_query}&count=20"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        gifs = data.get("gifs", [])
                        if not gifs:
                            await ctx.send(f"🔍 Nenhum GIF/Vídeo Redgifs encontrado para o termo: `{tags}`")
                            return

                        item = random.choice(gifs)
                        gif_url = item.get("urls", {}).get("sd") or item.get("urls", {}).get("hd")

                        embed = discord.Embed(
                            title=f"🔞 Redgifs: {tags.title()}",
                            description=f"🎥 Termo: `{tags}` | 👀 Views: {item.get('views', 0)}",
                            color=discord.Color.purple()
                        )
                        if gif_url:
                            embed.set_image(url=gif_url)
                            await ctx.send(embed=embed)
                        else:
                            await ctx.send(f"🔞 **Redgifs ({tags}):** https://www.redgifs.com/watch/{item.get('id')}")
                    else:
                        await ctx.send(f"🔞 **Redgifs ({tags}):** https://www.redgifs.com/gifs/{search_query}")
        except Exception as e:
            await ctx.send(f"❌ Erro ao buscar no Redgifs: {e}")

async def setup(bot):
    await bot.add_cog(NSFWCog(bot))
