import asyncio
import discord
from discord.ext import commands
from src.modules.rpg import RPGCog
from src.modules.management import ManagementCog
from src.modules.games import GamesCog
from src.modules.economy import EconomyCog
from src.modules.nsfw import NSFWCog
from src.modules.user_utils import UserUtilsCog

# Cache para deduplicação de mensagens
processed_message_ids = set()

class VanillaBot(commands.Bot):
    async def setup_hook(self):
        await self.add_cog(RPGCog(self))
        await self.add_cog(ManagementCog(self))
        await self.add_cog(GamesCog(self))
        await self.add_cog(EconomyCog(self))
        await self.add_cog(NSFWCog(self))
        await self.add_cog(UserUtilsCog(self))

def create_discord_bot(get_app_instance_func=None):
    """Cria e configura uma instância modular do Bot do Discord."""
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True
    intents.voice_states = True
    intents.message_content = True
    
    new_bot = VanillaBot(command_prefix="!", intents=intents, help_command=None)

    @new_bot.command(name="help", aliases=["ajuda"])
    async def help_cmd(ctx, category: str = None):
        """Sistema de ajuda geral e por categorias."""
        if not category:
            embed = discord.Embed(
                title="📜 Central de Ajuda - Bot Vanilla",
                description=(
                    "Bem-vindo à central de comandos! Use `!help {categoria}` para ver os comandos específicos.\n\n"
                    "📁 **Categorias Disponíveis:**\n"
                    "• `Gerenciamento` ➔ Boas-vindas e Despedidas com GIF/imagem\n"
                    "• `RPG` ➔ Rolagens de dados Rollem, comentários e Fichas de Inimigos\n"
                    "• `Jogos` ➔ Minigame de Poker 1d10 em DM, Moeda e Jogos de Mesa\n"
                    "• `Economia` ➔ Níveis, XP, Saldo de Moedas e Daily\n"
                    "• `NSFW` ➔ Imagens da Rule34 e Redgifs (Apenas canais NSFW)\n"
                    "• `USER` ➔ Cores de cargo e promoções\n"
                    "• `Voz` ➔ Conectar e transmitir áudio no canal de voz\n"
                ),
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return

        cat_clean = category.strip().lower()

        if cat_clean == "gerenciamento":
            embed = discord.Embed(title="⚙️ Categoria: Gerenciamento", color=discord.Color.green())
            embed.add_field(name="!set welcome to #canal", value="Define o canal de mensagens de boas-vindas.", inline=False)
            embed.add_field(name="!set goodbye to #canal", value="Define o canal de mensagens de despedida.", inline=False)
            await ctx.send(embed=embed)

        elif cat_clean == "rpg":
            embed = discord.Embed(title="🎲 Categoria: RPG & Dados", color=discord.Color.gold())
            embed.add_field(name="Rolagens de Dados", value="`1d20 [comentário]` | `3#5d20+2` | `1d4!` | `8d6ns` | `8d6++2` | `4d6d1` | `dF`", inline=False)
            embed.add_field(name="!set {Enemy Sheet}Name: \"...\" HP: X; AC: Y;", value="Cria uma ficha de inimigo.", inline=False)
            embed.add_field(name="!atk \"Nome\" X", value="Causa dano e atualiza a barra de vida.", inline=False)
            embed.add_field(name="!heal \"Nome\" X", value="Cura um inimigo.", inline=False)
            embed.add_field(name="!status \"Nome\"", value="Exibe ficha e barra de vida ASCII.", inline=False)
            embed.add_field(name="!delete_enemy \"Nome\"", value="Remove o inimigo.", inline=False)
            await ctx.send(embed=embed)

        elif cat_clean in ["jogos", "games"]:
            embed = discord.Embed(title="🃏 Categoria: Jogos & Minigames", color=discord.Color.purple())
            embed.add_field(name="!poker", value="Abre uma mesa de Poker 1d10.", inline=False)
            embed.add_field(name="!entrar_poker", value="Entra na partida de Poker.", inline=False)
            embed.add_field(name="!iniciar_poker", value="Inicia o sorteio de cartas privadas em DM e turnos da mesa.", inline=False)
            embed.add_field(name="!moeda", value="Sorteia Cara ou Coroa.", inline=False)
            await ctx.send(embed=embed)

        elif cat_clean in ["economia", "eco"]:
            embed = discord.Embed(title="💰 Categoria: Economia & Níveis", color=discord.Color.dark_gold())
            embed.add_field(name="!profile [@Membro]", value="Exibe seu nível, XP total e saldo de moedas.", inline=False)
            embed.add_field(name="!daily", value="Resgata suas moedas diárias.", inline=False)
            embed.add_field(name="!pay @Membro X", value="Transfere moedas para outro membro.", inline=False)
            await ctx.send(embed=embed)

        elif cat_clean == "nsfw":
            embed = discord.Embed(title="🔞 Categoria: NSFW (Canais NSFW)", color=discord.Color.red())
            embed.add_field(name="!r34 [tags]", value="Busca imagens na API da Rule34.", inline=False)
            embed.add_field(name="!redgifs [tags]", value="Busca GIFs na API da Redgifs.", inline=False)
            await ctx.send(embed=embed)

        elif cat_clean == "user":
            embed = discord.Embed(title="👤 Categoria: USER", color=discord.Color.teal())
            embed.add_field(name="!cor #HEX", value="Define a cor do seu cargo (ex: `!cor #FF0000`).", inline=False)
            embed.add_field(name="!promover @Membro @Cargo", value="Atribui um cargo a um membro.", inline=False)
            await ctx.send(embed=embed)

        elif cat_clean == "voz":
            embed = discord.Embed(title="🔊 Categoria: Voz & Transmissão", color=discord.Color.blue())
            embed.add_field(name="!start", value="Conecta ao seu canal de voz e inicia o streaming.", inline=False)
            embed.add_field(name="!stop", value="Para o streaming e sai do canal de voz.", inline=False)
            await ctx.send(embed=embed)

        else:
            await ctx.send(f"❌ Categoria `{category}` não encontrada. Use `!help` para ver a lista!")

    @new_bot.command(name="start", aliases=["iniciar", "entrar", "join"])
    async def start_cmd(ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ **Você precisa estar conectado a um canal de voz** no Discord para usar o comando `!start`!")
            return

        voice_channel = ctx.author.voice.channel
        await ctx.send(f"🔊 Conectando ao seu canal de voz: **{voice_channel.name}**...")

        app = get_app_instance_func() if get_app_instance_func else None
        if app:
            token = app.token_var.get().strip()
            audio_device = app.device_combobox.get()
            mode = app.mode_var.get()
            ffmpeg_bin = app.ffmpeg_path_var.get().strip()
            target_win = app.window_combobox.get()

            asyncio.create_task(
                app.async_start_stream(
                    token=token,
                    channel_id=voice_channel.id,
                    audio_device=audio_device,
                    mode=mode,
                    ffmpeg_bin=ffmpeg_bin,
                    target_channel=voice_channel,
                    target_win=target_win
                )
            )

    @new_bot.command(name="stop", aliases=["parar", "sair", "leave"])
    async def stop_cmd(ctx):
        app = get_app_instance_func() if get_app_instance_func else None
        if app:
            await ctx.send("🛑 **Encerrando a transmissão de áudio** e desconectando do canal de voz...")
            asyncio.create_task(app.async_stop_stream())

    @new_bot.event
    async def on_ready():
        print(f"Bot de Voz logado com sucesso no Discord: {new_bot.user}")
        try:
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name="!help | d20 RPG no chat"
            )
            await new_bot.change_presence(status=discord.Status.online, activity=activity)
        except Exception as e:
            print(f"Aviso ao definir presença de login do bot: {e}")

    @new_bot.event
    async def on_message(message):
        if message.author.bot:
            return

        if message.id in processed_message_ids:
            return
            
        processed_message_ids.add(message.id)
        if len(processed_message_ids) > 2000:
            processed_message_ids.clear()
            
        # Motor de Dados RPG (Estilo Rollem com regra de comentário prefixado)
        dice_results, repeat_count = RPGCog.parse_and_roll_dice(message.content)
        if dice_results:
            if repeat_count > 1:
                reply_txt = f"🎲 {message.author.mention}\n\n" + "\n\n".join(dice_results)
            else:
                reply_txt = f"🎲 {message.author.mention} " + " | ".join(dice_results)
            await message.channel.send(reply_txt)
            
        await new_bot.process_commands(message)

    return new_bot
