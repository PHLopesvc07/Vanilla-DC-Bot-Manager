import os
import discord
# pyrefly: ignore [missing-import]
from discord.ext import commands
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Recupera o token do arquivo .env
TOKEN = os.getenv("DISCORD_TOKEN")

# 1. Configurações básicas de permissão
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. Eventos (coisas que acontecem automaticamente)
@bot.event
async def on_ready():
    print(f"Bot online com sucesso como {bot.user}", flush=True)

# 3. Comandos simples (Lógica de resposta direta)
@bot.command()
async def ola(ctx):
    # ctx.author.mention menciona quem chamou o comando
    await ctx.send(f"Olá, {ctx.author.mention}! Como posso ajudar?")

# 4. Comandos com parâmetros e lógica matemática/condicional
@bot.command()
async def somar(ctx, num1: float, num2: float):
    resultado = num1 + num2
    await ctx.send(f"A soma de {num1} + {num2} é **{resultado}**")

# 5. Lógica com condições e regras
@bot.command()
async def sorteio(ctx):
    import random
    opcoes = ["Cara", "Coroa"]
    escolha = random.choice(opcoes)
    await ctx.send(f"O resultado da moeda foi: **{escolha}**!")

if __name__ == "__main__":
    if not TOKEN:
        print("Erro: A variável de ambiente DISCORD_TOKEN não está definida no arquivo .env!", flush=True)
    else:
        try:
            print("Iniciando o bot do Discord...", flush=True)
            bot.run(TOKEN)
        except discord.errors.LoginFailure:
            print("Erro: O token do Discord fornecido no arquivo .env é inválido ou expirado!", flush=True)
        except Exception as e:
            print(f"Erro ao iniciar o bot: {e}", flush=True)
