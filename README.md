# 🎙️ Discord Simple Bot Client (Vanilla Bot)

Uma aplicação desktop completa e modular em **Python** para gerenciar seu bot do Discord, jogar partidas de **Poker 1d10**, rodar o **Motor de Dados RPG Rollem**, gerenciar **Fichas de Inimigos**, controlar **Boas-Vindas/Despedidas com Imgur API** e transmitir **áudio de alta qualidade em tempo real** para canais de voz do Discord.

Possui uma interface gráfica moderna (estilo Discord Dark Theme) desenvolvida com **CustomTkinter**, botões visuais de **Ligar/Desligar Bot**, suporte a **Token Personalizado (BYOB - Bring Your Own Bot)**, isolamento de áudio por janela/aplicativo e controle por comandos no chat (`!start`, `!help`).

---

## 🌟 Principais Recursos

- 🔑 **Token Personalizado de Bot (Bring Your Own Bot)**: Permite inserir qualquer Token de bot próprio do Discord na interface gráfica, com botão de exibição/ocultação segura (`👁️`/`🔒`).
- ⚡ **Controle de Energia (Ligar/Desligar Bot)**: Conecte ou desconecte o Bot diretamente pela interface sem precisar abrir o terminal.
- 🗄️ **Banco de Dados SQLite Local (`vanilla_local.db`)**:
  - Armazenamento persistente de fichas de inimigos, economia/XP de usuários e configurações personalizadas de servidor (mensagens de boas-vindas/despedida).
  - Edição direta de fichas de criaturas pela própria interface desktop ou por comandos no Discord.
- 🎵 **Isolamento de Áudio de Janela/App**: Transmita **EXCLUSIVAMENTE o som do aplicativo selecionado** (ex: Chrome, Spotify, Jogos) sem capturar o áudio geral do sistema.
- 🚀 **Conexão Automática por Comando (`!start`)**: Basta entrar em um canal de voz no Discord e digitar `!start` no chat para o bot se conectar e iniciar o streaming.
- 🎲 **Motor RPG Rollem Completo**:
  - Suporta notações oficiais: `XdY`, `XdY!`, `XdYns`, `dado++valor`, `dado--valor`, `(expressão)`, `XdY*V`, `XdY/V`, `XdY<<V`, `XdY>>V`, `dF` (Fate), `N#Expressão` e `XdYdZ` / `XdYdhZ`.
  - **Regra de Comentário Prefixado**: A rolagem só é executada se a mensagem **iniciar obrigatoriamente** pelo dado (ex: `1d20 ataque de espada`). O comentário anexado possui limite de 20 caracteres.
- 🐉 **Gerenciador de Fichas de Inimigos/Criaturas**:
  - Criar fichas (`!set {Enemy Sheet}Name: "Nome"; HP: 50; AC: 15;`), Atacar (`!atk`), Curar (`!heal`), Status (`!status`), Marcar Morto (`!set status deceased`) e Deletar (`!delete_enemy`).
  - Barra de vida visual em blocos ASCII proporcional em tempo real (`~[-||||||||||||-----------------] 60%~`).
- 🃏 **Minigame de Poker 1d10 em DM**:
  - Partida interativa (`!poker`, `!entrar_poker`, `!iniciar_poker`).
  - Distribui `2#d10` privadas via **DM** para os participantes e revela 3 cartas da mesa (`1d10`) com rodadas de aposta/bluff por iniciativa.
  - Avaliador automático para as 10 combinações de mãos oficiais (Royal Flush até Carta Alta).
- 🖼️ **Gerenciamento de Boas-Vindas/Despedida com API do Imgur**:
  - `!set welcome to #canal` e `!set goodbye to #canal`.
  - Upload de imagens e GIFs via **Imgur API v3** com placeholders dinâmicos (`{user}`, `{user.name}`, `{channel}`, `{server}`, `{member_count}`).
- 💰 **Economia & Níveis**: XP por mensagens, Level Up, `!profile`, `!daily` (24h) e `!pay`.
- 🔞 **Integração NSFW Avançada com Filtro de Tags**:
  - Busca nas APIs Rule34 (`!r34 [tags] [gif/video]`) e Redgifs (`!redgifs [tag]`) com suporte a mídias e categorias (`femboy`, `trans`, `yaoi`, `yuri`, `hentai`, `video`, `gif`, etc.).
  - Trava obrigatória de canal NSFW (`ctx.channel.is_nsfw()`).
- 👤 **Utilidades USER**: Troca de cor de cargo (`!cor #HEX`) e atribuição de cargos (`!promover`).
- 📜 **Central de Ajuda por Categoria**: `!help` geral e por categorias (`!help rpg`, `!help gerenciamento`, `!help jogos`, etc.).

---

## 📜 Lista Completa de Comandos por Categoria

### ⚙️ Gerenciamento & Configuração do Server

| Comando | Sintaxe / Exemplo | Descrição |
| :--- | :--- | :--- |
| `!set welcome` | `!set welcome to #boas-vindas` | Define o canal de boas-vindas do servidor. |
| `!set goodbye` | `!set goodbye to #saidas` | Define o canal de despedidas do servidor. |
| `!config_welcome` | `!config_welcome [mensagem]` | Define o texto personalizado de entrada (`{user}`, `{server}`). |
| `!config_goodbye` | `!config_goodbye [mensagem]` | Define o texto personalizado de saída. |

---

### 🎲 RPG & Dados (Motor Rollem + SQLite Enemy Sheets)

| Comando | Sintaxe / Exemplo | Descrição |
| :--- | :--- | :--- |
| `XdY [comentário]` | `1d20+4 Espada Longa` | Rola dados com comentário prefixado (máx 20 chars). |
| `(Expressão)` | `((1d20+4)*3-4)/2 Espada` | Rola dados com prioridade matemática de parênteses, multiplicação e divisão. |
| `XdY!` | `1d4! Explicitação` | Dados explosivos (rola novamente ao tirar valor máximo). |
| `XdYns` | `8d6ns` | Rola os dados sem ordenar os resultados de forma crescente. |
| `dado++valor` / `dado--valor` | `1d20++5` / `1d20--3` | Incrementa ou decrementa o valor final de cada dado rolado. |
| `N#Expressão` | `3#1d20+2` | Rola N vezes a mesma expressão de dados em linhas separadas. |
| `!set {Enemy Sheet}` | `!set {Enemy Sheet}Name: "Goblin"; HP: 30; AC: 13;` | Registra uma nova ficha de inimigo no SQLite local. |
| `!atk` | `!atk "Goblin" 12` | Aplica dano ao HP do inimigo e atualiza o status visual. |
| `!heal` | `!heal "Goblin" 10` | Cura o HP do inimigo respeitando o limite máximo. |
| `!status` | `!status "Goblin"` | Exibe o cartão completo de status e barra de vida do inimigo. |
| `!delete_enemy` | `!delete_enemy "Goblin"` | Remove a ficha do inimigo do banco SQLite. |

---

### 🃏 Jogos & Poker 1d10

| Comando | Sintaxe / Exemplo | Descrição |
| :--- | :--- | :--- |
| `!poker` | `!poker` | Cria uma nova sala/mesa de Poker 1d10 no chat. |
| `!entrar_poker` | `!entrar_poker` | Entra na sala de poker aberta. |
| `!iniciar_poker` | `!iniciar_poker` | Inicia a partida e envia 2 cartas (`2#d10`) via DM para cada jogador. |
| `!moeda` | `!moeda` | Rola Cara ou Coroa no chat. |

---

### 💰 Economia & Perfil

| Comando | Sintaxe / Exemplo | Descrição |
| :--- | :--- | :--- |
| `!profile` | `!profile` ou `!profile @User` | Exibe o nível de XP, moedas e estatísticas do usuário. |
| `!daily` | `!daily` | Resgata a recompensa diária de moedas (Cooldown de 24 horas). |
| `!pay` | `!pay @User 100` | Transfere moedas da sua conta para outro usuário. |

---

### 🔞 NSFW (Rule34 & Redgifs com Tags Personalizadas)

| Comando | Sintaxe / Exemplo | Descrição |
| :--- | :--- | :--- |
| `!r34` | `!r34 hatsune miku video` ou `!r34 2b` | Busca mídias na Rule34 por qualquer personagem, anime, jogo ou tag. Espaços são automaticamente convertidos para `_`. |
| `!redgifs` | `!redgifs femboy` ou `!redgifs trans` | Busca GIFs/Vídeos no Redgifs por categoria ou termo. |
| `!nsfw_tags` | `!nsfw_tags` | Lista as tags comuns, categorias organizadas e sugestões de termos para busca de personagens. |

---

### 👤 USER & Utilidades

| Comando | Sintaxe / Exemplo | Descrição |
| :--- | :--- | :--- |
| `!cor` | `!cor #FF0000` | Altera a cor HEX do seu cargo exclusivo no servidor. |
| `!promover` | `!promover @User @Cargo` | Promove um membro atribuindo um cargo específico. |

---

### 🔊 Voz & Transmissão de Áudio

| Comando | Sintaxe / Exemplo | Descrição |
| :--- | :--- | :--- |
| `!start` | `!start` | Conecta o bot ao seu canal de voz atual e inicia o streaming de áudio. |
| `!stop` | `!stop` | Desconecta o bot do canal de voz e encerra o áudio. |

---

## 🛠️ Como Foi Feito (Arquitetura e Tecnologias)

### 1. Tecnologias Utilizadas
- **Python 3.12+**: Linguagem principal do projeto.
- **`discord.py`**: Framework assíncrono de integração com a API e Gateway do Discord.
- **CustomTkinter**: Interface gráfica nativa moderna com abas e tema escuro estilo Discord.
- **SoundDevice / PyNaCl**: Captura PCM nativa de 48kHz em blocos de 20ms com latência ultrabaixa.
- **Imgur API v3**: Serviço de hospedagem e upload anônimo de mídias (PNG, JPG, GIF).
- **PyInstaller**: Empacotador e compilador em executável autônomo `.exe`.

### 2. Estrutura Modular do Código (`src/`)
```text
Vanilla/
├── Vanilla-DC-Bot-Manager/
│   ├── voice_stream_app.py      # Ponto de entrada principal da Interface Gráfica CustomTkinter
│   ├── Iniciar_Programa.bat     # Atalho de inicialização rápida em 2 cliques
│   ├── dist/                    # Executável autônomo compilado (DiscordSimpleBotClient.exe)
│   ├── src/
│   │   ├── config.py            # Gerenciador de configurações e variáveis .env
│   │   ├── core/
│   │   │   ├── bot.py           # Instância modular do Bot, registro de eventos e Cogs
│   │   │   └── audio_engine.py  # Captura nativa de áudio PCM 48kHz via SoundDevice
│   │   ├── modules/
│   │   │   ├── rpg.py           # Motor Rollem, validação de comentários e EnemyManager
│   │   │   ├── management.py    # Boas-vindas/Despedida, Imgur API e placeholders
│   │   │   ├── games.py         # Minigame de Poker 1d10 (DM) e avaliador de mãos
│   │   │   ├── economy.py       # Sistema de XP, Níveis, Daily e Moedas
│   │   │   ├── nsfw.py          # Integrações Rule34 e Redgifs com trava NSFW
│   │   │   └── user_utils.py    # Gerenciamento de cores de cargos e promoções
│   │   ├── ui/
│   │   │   ├── app.py           # Janela principal CustomTkinter (CTkTabview)
│   │   │   └── tabs/
│   │   │       └── rpg_tab.py   # Aba visual da categoria RPG e guia de notações
│   │   └── utils/
│   │       ├── imgur_uploader.py # Helper assíncrono aiohttp para upload no Imgur API v3
│   │       ├── ffmpeg_finder.py  # Localizador automático de binários FFmpeg/DirectShow
│   │       └── system_info.py    # Mapeador de janelas e processos ativos no Windows
│   └── .env                     # Arquivo local de variáveis de ambiente e Token do Bot
└── README.md                    # Documentação oficial
```

---

## 🚀 Como Inicializar e Usar

### 🟢 Método 1: Executável Direto ou Atalho (Sem necessidade de VS Code)
1. Dê 2 cliques no arquivo **`Iniciar_Programa.bat`** (ou abra `dist/DiscordSimpleBotClient/DiscordSimpleBotClient.exe`).
2. A interface gráfica do **Discord Simple Bot Client** será aberta.

---

### 🟢 Método 2: Execução via Código Fonte (Python)
1. Instale as dependências executando no terminal:
   ```bash
   pip install -r requirements.txt
   ```
2. Execute o aplicativo:
   ```bash
   python voice_stream_app.py
   ```

---

## ⚡ Passo a Passo de Uso na Interface Gráfica

1. **Configurar o Bot**:
   - Abra a aba **`⚙️ Configurações & Bot`**.
   - Cole o Token do seu bot do Discord no campo **"Token do Bot"** (você pode clicar no ícone `👁️` para visualizar ou ocultar o Token).
2. **Ligar o Bot**:
   - No painel superior, clique em **`⚡ Ligar Bot`**. O indicador ficará verde 🟢 **Bot Ligado**.
3. **Usar no Discord**:
   - **Canal de Voz**: Entre em qualquer canal de voz no seu servidor e digite `!start` no chat de texto para o bot se conectar e transmitir áudio. Digite `!stop` para desconectar.
   - **Comandos de RPG**: Digite `1d20 ataque` no chat para rolar dados com comentário.
   - **Ficha de Inimigo**: Digite `!set {Enemy Sheet}Name: "Orc"; HP: 50; AC: 15;` e depois `!atk "Orc" 15`.
   - **Poker**: Digite `!poker`, peça para os jogadores digitarem `!entrar_poker` e depois `!iniciar_poker` para receber cartas em DM privada.
   - **Central de Ajuda**: Digite `!help` no chat para listar todos os comandos.
