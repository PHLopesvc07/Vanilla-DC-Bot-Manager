import random
import asyncio
import discord
from discord.ext import commands

def evaluate_poker_hand(cards_5: list[int]) -> tuple[int, str]:
    """
    Avalia 5 cartas (2 da mão + 3 da mesa) segundo a tabela do Vanilla Poker 1d10:
    1 - Royal Flush: valores são 6, 7, 8, 9 e 10
    2 - Straight Flush: qualquer sequência de 5 números (ex: 1, 2, 3, 4, 5)
    3 - 4 de um tipo (Quadra): 4 cartas repetidas
    4 - Full House: 3 de um tipo + 2 de outro
    5 - Flush: 5 cartas que são múltiplos de 3 (3, 6, 9, etc.)
    6 - Straight: 5 cartas que são múltiplos de 2 (2, 4, 6, 8, 10)
    7 - 3 de um tipo (Trinca): 3 cartas iguais
    8 - 2 pares: 2 de um número + 2 de outro número
    9 - Par: 2 cartas iguais
    10 - Carta Alta: maior carta isolada
    """
    sorted_cards = sorted(cards_5)
    counts = {}
    for c in sorted_cards:
        counts[c] = counts.get(c, 0) + 1

    count_values = sorted(counts.values(), reverse=True)

    # 1. Royal Flush: [6, 7, 8, 9, 10]
    if sorted_cards == [6, 7, 8, 9, 10]:
        return 1, "👑 Royal Flush (6, 7, 8, 9, 10)"

    # 2. Straight Flush: sequência de 5 números consecutivos
    is_sequence = all(sorted_cards[i] + 1 == sorted_cards[i+1] for i in range(4))
    if is_sequence:
        return 2, f"🌟 Straight Flush ({', '.join(map(str, sorted_cards))})"

    # 3. 4 de um tipo
    if 4 in count_values:
        return 3, "🔥 Quadra (4 de um tipo)"

    # 4. Full House (3 + 2)
    if count_values == [3, 2]:
        return 4, "🏠 Full House (Trinca + Par)"

    # 5. Flush: 5 cartas múltiplas de 3
    if all(c % 3 == 0 for c in sorted_cards):
        return 5, "✨ Flush (5 Múltiplos de 3)"

    # 6. Straight: 5 cartas múltiplas de 2
    if all(c % 2 == 0 for c in sorted_cards):
        return 6, "🎲 Straight (5 Múltiplos de 2)"

    # 7. 3 de um tipo
    if 3 in count_values:
        return 7, "⚡ Trinca (3 de um tipo)"

    # 8. 2 pares
    if count_values == [2, 2, 1]:
        return 8, "✌️ Dois Pares"

    # 9. Par
    if 2 in count_values:
        return 9, "👥 Um Par"

    # 10. Carta Alta
    high_card = sorted_cards[-1]
    return 10, f"🃏 Carta Alta ({high_card})"


class GamesCog(commands.Cog):
    """Módulo de Jogos e Minigames (Poker 1d10, Jogo da Velha, Blackjack)."""

    def __init__(self, bot):
        self.bot = bot
        self.active_poker_games = {} # channel_id -> state

    @commands.command(name="poker")
    async def poker_cmd(self, ctx):
        """Inicia uma partida de Poker 1d10 no canal."""
        if ctx.channel.id in self.active_poker_games:
            await ctx.send("❌ **Já existe uma partida de Poker em andamento neste canal!**")
            return

        guide = (
            "🃏 **Mesa de Poker 1d10 Iniciada!**\n"
            "```text\n"
            "Como jogar:\n"
            "1. Todos os participantes digitam '!entrar_poker' para se inscrever.\n"
            "2. O criador digita '!iniciar_poker' para sortear as cartas em DM privada.\n"
            "3. O bot revelará 3 cartas da mesa gradualmente a cada rodada de apostas.\n"
            "```"
        )
        self.active_poker_games[ctx.channel.id] = {
            "creator": ctx.author,
            "players": [ctx.author],
            "started": False,
            "private_hands": {}, # player_id -> [d10, d10]
            "table_cards": []
        }
        await ctx.send(guide)
        await ctx.send(f"👤 {ctx.author.mention} abriu a mesa! Outros jogadores: digitem `!entrar_poker`")

    @commands.command(name="entrar_poker", aliases=["entrarpoker"])
    async def entrar_poker(self, ctx):
        game = self.active_poker_games.get(ctx.channel.id)
        if not game:
            await ctx.send("❌ Nenhuma mesa de Poker aberta. Use `!poker` para abrir uma!")
            return

        if game["started"]:
            await ctx.send("❌ A partida já foi iniciada!")
            return

        if ctx.author in game["players"]:
            await ctx.send("⚠️ Você já está inscrito nesta mesa!")
            return

        game["players"].append(ctx.author)
        await ctx.send(f"✅ {ctx.author.mention} entrou na partida de Poker! Total de jogadores: {len(game['players'])}")

    @commands.command(name="iniciar_poker", aliases=["iniciarpoker"])
    async def iniciar_poker(self, ctx):
        game = self.active_poker_games.get(ctx.channel.id)
        if not game:
            await ctx.send("❌ Nenhuma mesa de Poker aberta.")
            return

        if game["started"]:
            await ctx.send("❌ Partida já iniciada!")
            return

        if len(game["players"]) < 1:
            await ctx.send("❌ Mínimo de 1 jogador necessário!")
            return

        game["started"] = True
        await ctx.send("🎰 **Distribuindo cartas privadas em DM para todos os participantes...**")

        # Rola 2#d10 no privado de cada jogador
        for p in game["players"]:
            c1, c2 = random.randint(1, 10), random.randint(1, 10)
            game["private_hands"][p.id] = [c1, c2]
            try:
                await p.send(
                    f"🃏 **Suas cartas privadas de Poker 1d10 no servidor {ctx.guild.name}:**\n"
                    f"Carta 1: **[{c1}]** | Carta 2: **[{c2}]**\n"
                    f"Mantenha em segredo dos outros jogadores!"
                )
            except Exception:
                await ctx.send(f"⚠️ Não foi possível enviar DM para {p.mention}! Verifique se as mensagens privadas estão abertas.")

        await ctx.send("💬 **1º Turno:** Cartas privadas distribuídas! Façam suas apostas/conversas. A 1ª carta da mesa será revelada em breve...")
        await asyncio.sleep(5)

        # Revela 1ª carta da mesa
        t1 = random.randint(1, 10)
        game["table_cards"].append(t1)
        await ctx.send(f"🎴 **1ª Carta da Mesa Revelada:** **[{t1}]**")

        await ctx.send("💬 **2º Turno:** Apostem ou aumentem o pote! A 2ª carta da mesa será revelada...")
        await asyncio.sleep(5)

        # Revela 2ª carta da mesa
        t2 = random.randint(1, 10)
        game["table_cards"].append(t2)
        await ctx.send(f"🎴 **2ª Carta da Mesa Revelada:** **[{t1}]**, **[{t2}]**")

        await ctx.send("💬 **3º Turno:** Última rodada de apostas antes da revelação final...")
        await asyncio.sleep(5)

        # Revela 3ª carta da mesa
        t3 = random.randint(1, 10)
        game["table_cards"].append(t3)
        await ctx.send(f"🎴 **3ª Carta da Mesa Revelada:** **[{t1}]**, **[{t2}]**, **[{t3}]**")

        # Conclusão e Avaliação das Mãos
        results = []
        for p in game["players"]:
            priv = game["private_hands"].get(p.id, [1, 1])
            all_5 = priv + game["table_cards"]
            rank_score, hand_name = evaluate_poker_hand(all_5)
            results.append({
                "player": p,
                "score": rank_score,
                "hand_name": hand_name,
                "priv": priv
            })

        # Ordena pelo menor rank_score (1 é melhor que 10)
        results.sort(key=lambda x: x["score"])
        winner = results[0]

        summary = f"🏆 **CONCLUSÃO DA PARTIDA DE POKER!** 🏆\n"
        summary += f"🎴 **Cartas da Mesa:** [{t1}], [{t2}], [{t3}]\n\n"

        for r in results:
            summary += f"• {r['player'].mention}: Mão [{r['priv'][0]}, {r['priv'][1]}] ➔ **{r['hand_name']}**\n"

        summary += f"\n🎉 **Vencedor:** {winner['player'].mention} com **{winner['hand_name']}**!"
        await ctx.send(summary)

        # Limpa partida
        self.active_poker_games.pop(ctx.channel.id, None)

    @commands.command(name="moeda", aliases=["flipcoin"])
    async def moeda_cmd(self, ctx):
        res = random.choice(["Cara", "Coroa"])
        await ctx.send(f"🪙 O resultado da moeda foi: **{res}**!")

async def setup(bot):
    await bot.add_cog(GamesCog(bot))
