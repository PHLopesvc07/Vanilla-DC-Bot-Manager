import os
import sys
import asyncio
import threading
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import discord
import sounddevice as sd

from src.config import get_env_var, save_env_var
from src.database import get_db_connection
from src.utils.ffmpeg_finder import find_ffmpeg, get_dshow_audio_devices
from src.utils.system_info import get_active_windows_with_process
from src.utils.imgur_uploader import ImgurUploader
from src.core.audio_engine import SoundDeviceAudioSource
from src.core.bot import create_discord_bot
from src.ui.tabs.rpg_tab import build_rpg_tab

# Configurações globais do CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

app_instance = None

def get_current_app():
    return app_instance


class VoiceStreamApp(ctk.CTk):
    def __init__(self, bot_instance, loop):
        super().__init__()
        
        global app_instance
        app_instance = self
        
        self.bot = bot_instance
        self.bot_loop = loop
        self.voice_client = None
        self.current_stream = None
        
        # Configurações da Janela
        self.title("Discord Simple Bot Client - Vanilla Manager")
        self.geometry("780x880")
        self.resizable(False, False)
        
        # Protocolo de Fechamento Gracioso
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Variáveis do formulário
        saved_ffmpeg = get_env_var("FFMPEG_PATH")
        detected_ffmpeg = find_ffmpeg() if (not saved_ffmpeg or saved_ffmpeg == "ffmpeg") else saved_ffmpeg
            
        self.token_var = tk.StringVar(value=get_env_var("DISCORD_TOKEN"))
        self.channel_id_var = tk.StringVar(value=get_env_var("DISCORD_CHANNEL_ID"))
        self.ffmpeg_path_var = tk.StringVar(value=detected_ffmpeg)
        self.mode_var = tk.StringVar(value="Nativo (SoundDevice - Sem FFmpeg)")
        self.status_var = tk.StringVar(value="Bot Desligado")
        self.is_token_visible = False

        # Variáveis de Boas-Vindas e Despedida
        self.welcome_msg_var = tk.StringVar(value=get_env_var("WELCOME_MSG", "🎉 Seja bem-vindo(a) ao {server}, {user}! Somos {member_count} membros!"))
        self.goodbye_msg_var = tk.StringVar(value=get_env_var("GOODBYE_MSG", "👋 {user.name} saiu do servidor {server}."))
        self.welcome_img_var = tk.StringVar(value=get_env_var("WELCOME_IMAGE_URL", ""))
        self.goodbye_img_var = tk.StringVar(value=get_env_var("GOODBYE_IMAGE_URL", ""))

        # Construção da Interface
        self.create_widgets()
        
        # Carrega listas
        self.refresh_windows()
        self.refresh_audio_devices()

        # Verifica estado inicial do bot
        if self.bot and self.bot.is_ready():
            self.on_bot_turned_on()
        elif get_env_var("DISCORD_TOKEN"):
            self.update_gui_status("Conectando Bot...", "#f0b232")
            self.after(2000, self.check_initial_bot_status)

    def check_initial_bot_status(self):
        if self.bot and self.bot.is_ready():
            self.on_bot_turned_on()

    def toggle_token_visibility(self):
        self.is_token_visible = not self.is_token_visible
        if self.is_token_visible:
            self.token_entry.configure(show="")
            self.btn_show_token.configure(text="🔒")
        else:
            self.token_entry.configure(show="*")
            self.btn_show_token.configure(text="👁️")

    def create_widgets(self):
        # BANNER SUPERIOR COM CONTROLES DE ENERGIA
        banner_frame = ctk.CTkFrame(self, corner_radius=12, height=85, fg_color="#1e1f22")
        banner_frame.pack(fill="x", padx=15, pady=(12, 6))
        banner_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            banner_frame, 
            text="Discord Simple Bot Client", 
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#5865F2"
        )
        title_label.pack(side="left", padx=15, pady=18)

        # Botões Ligar/Desligar
        power_frame = ctk.CTkFrame(banner_frame, fg_color="transparent")
        power_frame.pack(side="right", padx=15, pady=15)

        self.btn_turn_on = ctk.CTkButton(
            power_frame,
            text="⚡ Ligar Bot",
            fg_color="#248046",
            hover_color="#1a6535",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=105,
            height=32,
            command=self.turn_on_bot
        )
        self.btn_turn_on.pack(side="left", padx=4)

        self.btn_turn_off = ctk.CTkButton(
            power_frame,
            text="🔌 Desligar Bot",
            fg_color="#da373c",
            hover_color="#a92b2f",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=105,
            height=32,
            state="disabled",
            command=self.turn_off_bot
        )
        self.btn_turn_off.pack(side="left", padx=4)
        
        # BANNER DE STATUS
        sub_banner = ctk.CTkFrame(self, corner_radius=8, fg_color="#2b2d31", height=32)
        sub_banner.pack(fill="x", padx=15, pady=(0, 8))
        sub_banner.pack_propagate(False)
        
        self.status_dot = ctk.CTkLabel(sub_banner, text="●", text_color="#f23f43", font=ctk.CTkFont(size=18))
        self.status_dot.pack(side="left", padx=(12, 4))
        
        self.status_label = ctk.CTkLabel(sub_banner, textvariable=self.status_var, font=ctk.CTkFont(size=12, weight="bold"))
        self.status_label.pack(side="left", padx=(0, 12))

        # MENU PRINCIPAL DE CATEGORIAS (TABVIEW)
        self.tabview = ctk.CTkTabview(
            self, 
            corner_radius=12, 
            fg_color="#2b2d31",
            segmented_button_fg_color="#1e1f22",
            segmented_button_selected_color="#5865F2",
            segmented_button_selected_hover_color="#4752C4",
            segmented_button_unselected_color="#2b2d31",
            segmented_button_unselected_hover_color="#35373c"
        )
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(0, 12))

        # Categorias de Ação
        self.tab_audio = self.tabview.add("🎵 Streaming & Janela")
        self.tab_rpg = self.tabview.add("🎲 RPG & Dados")
        self.tab_config = self.tabview.add("⚙️ Configurações & Bot")
        self.tab_nsfw = self.tabview.add("🔞 NSFW & Tags")
        self.tab_help = self.tabview.add("💡 Guia de Áudio")

        self.tabview._segmented_button.configure(font=ctk.CTkFont(size=12, weight="bold"))

        # Construção do conteúdo das categorias
        self.build_audio_category()
        build_rpg_tab(self.tab_rpg)
        self.build_config_category()
        self.build_nsfw_category()
        self.build_help_category()

        # BARRA DE AÇÃO FIXA INFERIOR
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", side="bottom", padx=15, pady=(0, 12))
        
        self.start_button = ctk.CTkButton(
            action_frame, 
            text="▶ Iniciar Transmissão", 
            fg_color="#248046",
            hover_color="#1a6535",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            command=self.start_streaming
        )
        self.start_button.pack(fill="x", side="left", expand=True, padx=(0, 6))
        
        self.stop_button = ctk.CTkButton(
            action_frame, 
            text="⏹ Parar Transmissão", 
            fg_color="#da373c",
            hover_color="#a92b2f",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42,
            state="disabled",
            command=self.stop_streaming
        )
        self.stop_button.pack(fill="x", side="right", expand=True, padx=(6, 0))

    # --- CONTEÚDO DAS DEMAIS CATEGORIAS ---
    def build_audio_category(self):
        container = ctk.CTkScrollableFrame(self.tab_audio, fg_color="transparent")
        container.pack(fill="both", expand=True)

        win_frame = ctk.CTkFrame(container, corner_radius=10)
        win_frame.pack(fill="x", pady=6)
        
        ctk.CTkLabel(win_frame, text="1. APLICAÇÃO / JANELA ALVO A TRANSMITIR", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))
        
        w_sub = ctk.CTkFrame(win_frame, fg_color="transparent")
        w_sub.pack(fill="x", padx=15, pady=2)
        ctk.CTkLabel(w_sub, text="Janela / Processo Ativo:", font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkButton(w_sub, text="Recarregar Janelas", width=120, height=22, command=self.refresh_windows).pack(side="right")
        
        self.window_combobox = ctk.CTkComboBox(win_frame, values=["Procurando janelas..."])
        self.window_combobox.pack(fill="x", padx=15, pady=(0, 10))

        iso_card = ctk.CTkFrame(win_frame, corner_radius=8, fg_color="#1e1f22")
        iso_card.pack(fill="x", padx=15, pady=(0, 12))
        
        ctk.CTkLabel(iso_card, text="🎯 ISOLAMENTO DE SOM DE JANELA", font=ctk.CTkFont(size=11, weight="bold"), text_color="#f0b232").pack(anchor="w", padx=12, pady=(8, 2))
        iso_info = (
            "Abra as Configurações de Volume do Windows e altere a Saída de Som da janela\n"
            "selecionada para o dispositivo de entrada abaixo. Transmitirá APENAS essa janela!"
        )
        ctk.CTkLabel(iso_card, text=iso_info, font=ctk.CTkFont(size=11), justify="left", anchor="w").pack(anchor="w", padx=12, pady=(0, 6))
        ctk.CTkButton(
            iso_card, 
            text="🎛️ Abrir Configurações de Volume de Apps do Windows", 
            fg_color="#3b4252",
            hover_color="#434c5e",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=26,
            command=self.open_app_volume_settings
        ).pack(fill="x", padx=12, pady=(0, 8))

        dev_frame = ctk.CTkFrame(container, corner_radius=10)
        dev_frame.pack(fill="x", pady=6)
        
        ctk.CTkLabel(dev_frame, text="2. CAPTURA DE ÁUDIO E MOTOR", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(10, 4))
        
        ctk.CTkLabel(dev_frame, text="Modo de Transmissão:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15)
        self.mode_combobox = ctk.CTkComboBox(
            dev_frame, 
            values=["Nativo (SoundDevice - Sem FFmpeg)", "FFmpeg (DirectShow - Avançado)"],
            variable=self.mode_var,
            command=self.on_mode_change
        )
        self.mode_combobox.pack(fill="x", padx=15, pady=(0, 8))

        d_sub = ctk.CTkFrame(dev_frame, fg_color="transparent")
        d_sub.pack(fill="x", padx=15, pady=2)
        ctk.CTkLabel(d_sub, text="Dispositivo de Entrada de Áudio:", font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkButton(d_sub, text="Atualizar Dispositivos", width=130, height=22, command=self.refresh_audio_devices).pack(side="right")
        
        self.device_combobox = ctk.CTkComboBox(dev_frame, values=["Procurando dispositivos..."])
        self.device_combobox.pack(fill="x", padx=15, pady=(0, 12))

    def build_config_category(self):
        container = ctk.CTkScrollableFrame(self.tab_config, fg_color="transparent")
        container.pack(fill="both", expand=True)

        card_conn = ctk.CTkFrame(container, corner_radius=10)
        card_conn.pack(fill="x", pady=6)
        
        ctk.CTkLabel(card_conn, text="🔑 CREDENCIAIS DO BOT E CANAIS", font=ctk.CTkFont(size=13, weight="bold"), text_color="#5865F2").pack(anchor="w", padx=15, pady=(10, 4))
        
        ctk.CTkLabel(card_conn, text="Token do Bot (Token de qualquer Bot seu):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=15)
        
        token_sub = ctk.CTkFrame(card_conn, fg_color="transparent")
        token_sub.pack(fill="x", padx=15, pady=(0, 8))
        
        self.token_entry = ctk.CTkEntry(token_sub, textvariable=self.token_var, placeholder_text="Cole o Token do seu Bot aqui...", show="*")
        self.token_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        
        self.btn_show_token = ctk.CTkButton(
            token_sub, text="👁️", width=36, height=28,
            command=self.toggle_token_visibility
        )
        self.btn_show_token.pack(side="right")

        btn_save_token = ctk.CTkButton(
            card_conn, text="💾 Salvar Token", fg_color="#5865F2", hover_color="#4752C4",
            command=self.save_token_action
        )
        btn_save_token.pack(fill="x", padx=15, pady=(0, 12))

        # Card de Tutorial: Como obter seu Token do Discord Bot
        card_tutorial = ctk.CTkFrame(container, corner_radius=10, fg_color="#1e1f22")
        card_tutorial.pack(fill="x", pady=6)

        ctk.CTkLabel(card_tutorial, text="📖 PASSO A PASSO: COMO OBTER O TOKEN DO SEU BOT NO DISCORD", font=ctk.CTkFont(size=12, weight="bold"), text_color="#f0b232").pack(anchor="w", padx=15, pady=(10, 4))
        
        tutorial_text = (
            "1. Acesse o **Portal de Desenvolvedores do Discord**: https://discord.com/developers/applications\n"
            "2. Clique no botão **'New Application'** (Nova Aplicação) no canto superior direito e dê um nome ao seu Bot.\n"
            "3. No menu lateral esquerdo, clique na aba **'Bot'**.\n"
            "4. Na seção Token, clique no botão **'Reset Token'** e copie a chave gerada.\n"
            "5. **IMPORTANTE (Intents Obligatórias)**: Role a página até a seção **'Privileged Gateway Intents'** e ATIVE as 3 opções abaixo:\n"
            "   ✅ **PRESENCE INTENT**\n"
            "   ✅ **SERVER MEMBERS INTENT**\n"
            "   ✅ **MESSAGE CONTENT INTENT** (Essencial para o motor RPG e comandos)\n"
            "6. Cole o Token copiado no campo acima e clique em **'⚡ Ligar Bot'**."
        )
        ctk.CTkLabel(card_tutorial, text=tutorial_text, font=ctk.CTkFont(size=11), justify="left", anchor="w").pack(anchor="w", padx=15, pady=(0, 10))

        # Configuração de Mensagens de Boas-Vindas e Despedidas
        card_welcome = ctk.CTkFrame(container, corner_radius=10)
        card_welcome.pack(fill="x", pady=6)
        
        ctk.CTkLabel(card_welcome, text="🎉 CONFIGURAÇÃO DE BOAS-VINDAS E DESPEDIDAS", font=ctk.CTkFont(size=13, weight="bold"), text_color="#248046").pack(anchor="w", padx=15, pady=(10, 4))

        ctk.CTkLabel(card_welcome, text="Mensagem de Boas-Vindas (Use {user}, {server}, {member_count}):", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15)
        ctk.CTkEntry(card_welcome, textvariable=self.welcome_msg_var).pack(fill="x", padx=15, pady=(0, 6))

        wel_sub = ctk.CTkFrame(card_welcome, fg_color="transparent")
        wel_sub.pack(fill="x", padx=15, pady=(0, 8))
        ctk.CTkEntry(wel_sub, textvariable=self.welcome_img_var, placeholder_text="URL da imagem/GIF do Imgur...").pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(wel_sub, text="📤 Upload Imgur", width=110, command=self.upload_welcome_image).pack(side="right")

        ctk.CTkLabel(card_welcome, text="Mensagem de Despedida:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15)
        ctk.CTkEntry(card_welcome, textvariable=self.goodbye_msg_var).pack(fill="x", padx=15, pady=(0, 6))

        god_sub = ctk.CTkFrame(card_welcome, fg_color="transparent")
        god_sub.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkEntry(god_sub, textvariable=self.goodbye_img_var, placeholder_text="URL da imagem/GIF do Imgur...").pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(god_sub, text="📤 Upload Imgur", width=110, command=self.upload_goodbye_image).pack(side="right")

        def save_welcome_configs():
            save_env_var("WELCOME_MSG", self.welcome_msg_var.get())
            save_env_var("GOODBYE_MSG", self.goodbye_msg_var.get())
            save_env_var("WELCOME_IMAGE_URL", self.welcome_img_var.get())
            save_env_var("GOODBYE_IMAGE_URL", self.goodbye_img_var.get())
            messagebox.showinfo("Configurações Salvas", "✅ Mensagens e mídias salvas com sucesso!")

        ctk.CTkButton(card_welcome, text="💾 Salvar Configurações de Mensagens", fg_color="#248046", command=save_welcome_configs).pack(fill="x", padx=15, pady=(0, 12))

    def upload_welcome_image(self):
        filename = filedialog.askopenfilename(
            title="Selecione uma Imagem/GIF de Boas-Vindas",
            filetypes=[("Imagens e GIFs", "*.png;*.jpg;*.jpeg;*.gif"), ("Todos os arquivos", "*.*")]
        )
        if filename:
            try:
                with open(filename, "rb") as f:
                    data = f.read()
                link = asyncio.run_coroutine_threadsafe(
                    ImgurUploader.upload_image_bytes(data, os.path.basename(filename)),
                    self.bot_loop
                ).result(timeout=10.0)
                if link:
                    self.welcome_img_var.set(link)
                    save_env_var("WELCOME_IMAGE_URL", link)
                    messagebox.showinfo("Sucesso", f"Upload para Imgur concluído com sucesso!\nURL: {link}")
                else:
                    messagebox.showerror("Erro", "Falha ao realizar upload para o Imgur.")
            except Exception as e:
                messagebox.showerror("Erro de Upload", f"Ocorreu um erro no upload: {e}")

    def upload_goodbye_image(self):
        filename = filedialog.askopenfilename(
            title="Selecione uma Imagem/GIF de Despedida",
            filetypes=[("Imagens e GIFs", "*.png;*.jpg;*.jpeg;*.gif"), ("Todos os arquivos", "*.*")]
        )
        if filename:
            try:
                with open(filename, "rb") as f:
                    data = f.read()
                link = asyncio.run_coroutine_threadsafe(
                    ImgurUploader.upload_image_bytes(data, os.path.basename(filename)),
                    self.bot_loop
                ).result(timeout=10.0)
                if link:
                    self.goodbye_img_var.set(link)
                    save_env_var("GOODBYE_IMAGE_URL", link)
                    messagebox.showinfo("Sucesso", f"Upload para Imgur concluído com sucesso!\nURL: {link}")
                else:
                    messagebox.showerror("Erro", "Falha ao realizar upload para o Imgur.")
            except Exception as e:
                messagebox.showerror("Erro de Upload", f"Ocorreu um erro no upload: {e}")

    def build_nsfw_category(self):
        container = ctk.CTkScrollableFrame(self.tab_nsfw, fg_color="transparent")
        container.pack(fill="both", expand=True)

        card_tags = ctk.CTkFrame(container, corner_radius=10)
        card_tags.pack(fill="x", pady=6)
        
        ctk.CTkLabel(card_tags, text="🔞 CATEGORIAS E BUSCA DE MÍDIAS NSFW", font=ctk.CTkFont(size=13, weight="bold"), text_color="#da373c").pack(anchor="w", padx=15, pady=(10, 4))
        
        txt_nsfw = (
            "Selecione ou consulte as categorias e tags suportadas nos comandos de chat (`!r34` e `!redgifs`):\n\n"
            "   🔥  Categorias Populares: femboy, trans, yaoi, yuri, hentai, anime, real, cosplay\n"
            "   🎥  Filtros de Mídia: gif, video\n\n"
            "💬 Exemplos de comandos no Discord:\n"
            "   • !r34 femboy            ➔ Busca imagens com tag femboy na Rule34\n"
            "   • !r34 trans gif         ➔ Busca GIFs da categoria trans na Rule34\n"
            "   • !r34 yaoi              ➔ Busca imagens da categoria Yaoi na Rule34\n"
            "   • !redgifs femboy video  ➔ Busca vídeos/GIFs Redgifs\n"
        )
        ctk.CTkLabel(card_tags, text=txt_nsfw, font=ctk.CTkFont(size=11), justify="left", anchor="w").pack(anchor="w", padx=15, pady=(0, 12))

    def build_help_category(self):
        container = ctk.CTkScrollableFrame(self.tab_help, fg_color="transparent")
        container.pack(fill="both", expand=True)

        card_help = ctk.CTkFrame(container, corner_radius=10)
        card_help.pack(fill="x", pady=6)
        
        ctk.CTkLabel(card_help, text="💡 GUIA PASSO A PASSO DE ROTEAMENTO DE ÁUDIO", font=ctk.CTkFont(size=13, weight="bold"), text_color="#f0b232").pack(anchor="w", padx=15, pady=(10, 4))
        
        txt_guide = (
            "1. TRANSMITIR O SOM DE UM APP ESPECÍFICO (SEM SOM GERAL):\n"
            "   • Abra as Configurações de Volume de Apps do Windows abaixo.\n"
            "   • Mude a Saída de Som do seu app (ex: Chrome/Spotify) para um cabo virtual (Voice.ai / HitPaw / VB-Cable).\n"
            "   • Na aba 'Streaming & Janela', selecione esse mesmo cabo virtual como entrada.\n\n"
            "2. TRANSMITIR O SEU MICROFONE:\n"
            "   • Na aba 'Streaming & Janela', selecione o seu microfone físico no campo de dispositivo.\n\n"
            "3. USAR MIXAGEM ESTÉREO NATIVA DO WINDOWS:\n"
            "   • Ative a Mixagem Estéreo no Painel de Som do Windows abaixo.\n"
            "   • Selecione 'Mixagem Estéreo' no menu de dispositivos."
        )
        ctk.CTkLabel(card_help, text=txt_guide, font=ctk.CTkFont(size=11), justify="left", anchor="w").pack(anchor="w", padx=15, pady=(0, 10))

        btn_row = ctk.CTkFrame(card_help, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(0, 12))
        
        ctk.CTkButton(
            btn_row, 
            text="⚙️ Abrir Painel de Som (Mixagem Estéreo)", 
            fg_color="#4f545c",
            hover_color="#686d73",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28,
            command=self.open_sound_panel
        ).pack(side="left", expand=True, fill="x", padx=(0, 4))

        ctk.CTkButton(
            btn_row, 
            text="🎛️ Abrir Volume de Apps (Isolação)", 
            fg_color="#3b4252",
            hover_color="#434c5e",
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28,
            command=self.open_app_volume_settings
        ).pack(side="right", expand=True, fill="x", padx=(4, 0))

    # --- LÓGICA DE CONTROLE DE ENERGIA E TOKEN DO BOT ---
    def save_token_action(self):
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("Token Ausente", "Por favor, digite ou cole um Token válido antes de salvar.")
            return
        save_env_var("DISCORD_TOKEN", token)
        messagebox.showinfo("Token Salvo", "✅ Token do Bot salvo com sucesso no seu perfil de usuário local!")

    async def validate_discord_token(self, token: str) -> bool:
        """Valida o Token fazendo uma requisição rápida de teste à API do Discord."""
        url = "https://discord.com/api/v10/users/@me"
        headers = {"Authorization": f"Bot {token}"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def turn_on_bot(self):
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("Token Ausente", "Por favor, insira o Token do Discord Bot para ligar.")
            self.tabview.set("⚙️ Configurações & Bot")
            return

        # Salva o token automaticamente ao ligar
        save_env_var("DISCORD_TOKEN", token)
        self.btn_turn_on.configure(state="disabled")
        self.update_gui_status("Validando Token...", "#f0b232")
        asyncio.run_coroutine_threadsafe(self.async_turn_on_bot(token), self.bot_loop)

    async def async_turn_on_bot(self, token):
        try:
            # 1. Pré-validação rápida do Token via API HTTP do Discord
            is_valid = await self.validate_discord_token(token)
            if not is_valid:
                self.after(0, self.on_bot_turn_on_failed, "🔑 Token inválido! Verifique se copiou a chave correta no Portal de Desenvolvedores do Discord.")
                return

            self.after(0, lambda: self.update_gui_status("Conectando Bot...", "#f0b232"))

            if self.bot.is_closed():
                self.bot = create_discord_bot(get_current_app)
                
            if not self.bot.is_ready():
                print("Conectando Bot ao Discord Gateway...")
                asyncio.create_task(self.bot.start(token))
                
                for _ in range(30):
                    if self.bot.is_ready():
                        break
                    await asyncio.sleep(0.5)
                    
                if not self.bot.is_ready():
                    self.after(0, self.on_bot_turn_on_failed, "O bot não conseguiu conectar ao gateway. Verifique sua conexão ou se as 3 Privileged Intents estão ativadas.")
                    return

            self.after(0, self.on_bot_turned_on)
        except Exception as e:
            self.after(0, self.on_bot_turn_on_failed, f"Erro ao ligar o bot: {e}")

    def on_bot_turned_on(self):
        self.update_gui_status("Bot Ligado (Pronto para !start)", "#23a55a")
        self.btn_turn_on.configure(state="disabled")
        self.btn_turn_off.configure(state="normal")

    def on_bot_turn_on_failed(self, err_msg):
        messagebox.showerror("Erro ao Ligar Bot", err_msg)
        self.update_gui_status("Bot Desligado", "#f23f43")
        self.btn_turn_on.configure(state="normal")
        self.btn_turn_off.configure(state="disabled")

    def turn_off_bot(self):
        self.btn_turn_off.configure(state="disabled")
        self.update_gui_status("Desconectando Bot...", "#f0b232")
        asyncio.run_coroutine_threadsafe(self.async_turn_off_bot(), self.bot_loop)

    async def async_turn_off_bot(self):
        try:
            if self.voice_client and self.voice_client.is_connected():
                if self.voice_client.is_playing():
                    self.voice_client.stop()
                await self.voice_client.disconnect()
                self.voice_client = None
                self.current_stream = None

            if self.bot and not self.bot.is_closed():
                await self.bot.close()

            self.after(0, self.on_bot_turned_off)
        except Exception as e:
            print(f"Erro ao desligar bot: {e}")
            self.after(0, self.on_bot_turned_off)

    def on_bot_turned_off(self):
        self.update_gui_status("Bot Desligado", "#f23f43")
        self.btn_turn_on.configure(state="normal")
        self.btn_turn_off.configure(state="disabled")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    # --- AÇÕES DA INTERFACE ---
    def open_sound_panel(self):
        try:
            subprocess.Popen(["control", "mmsys.cpl", "sounds"])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o Painel de Som do Windows: {e}")

    def open_app_volume_settings(self):
        try:
            subprocess.Popen(['cmd', '/c', 'start', 'ms-settings:apps-volume'])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir as configurações de som de apps do Windows: {e}")

    def on_mode_change(self, choice):
        self.refresh_audio_devices()

    def refresh_windows(self):
        try:
            window_list = get_active_windows_with_process()
            self.window_combobox.configure(values=window_list)
            self.window_combobox.set(window_list[0])
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao listar as janelas ativas: {e}")

    def refresh_audio_devices(self):
        try:
            mode = self.mode_var.get()
            cleaned_devices = []

            if "FFmpeg" in mode:
                ffmpeg_bin = self.ffmpeg_path_var.get().strip()
                cleaned_devices = get_dshow_audio_devices(ffmpeg_bin)

            if not cleaned_devices:
                devices = sd.query_devices()
                input_devs = []
                for d in devices:
                    if d['max_input_channels'] > 0:
                        raw_name = d['name']
                        base_name = raw_name.split(", ")[0].strip()
                        if base_name and base_name not in input_devs:
                            input_devs.append(base_name)
                cleaned_devices = sorted(input_devs)

            if not cleaned_devices:
                cleaned_devices = ["Nenhum dispositivo encontrado"]
            
            default_selection = cleaned_devices[0]
            for dev in cleaned_devices:
                dev_lower = dev.lower()
                if "voice.ai" in dev_lower or "hitpaw" in dev_lower or "voicemod" in dev_lower or "cable" in dev_lower or "virtual" in dev_lower:
                    default_selection = dev
                    break
                elif "mixagem" in dev_lower or "stereo mix" in dev_lower or "mixed capture" in dev_lower:
                    default_selection = dev
                elif "microfone" in dev_lower or "microphone" in dev_lower:
                    default_selection = dev

            self.device_combobox.configure(values=cleaned_devices)
            self.device_combobox.set(default_selection)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao listar dispositivos de áudio: {e}")

    def browse_ffmpeg(self):
        filename = filedialog.askopenfilename(
            title="Selecione o executável do FFmpeg (ffmpeg.exe)",
            filetypes=[("Executável FFmpeg", "ffmpeg.exe"), ("Todos os arquivos", "*.*")]
        )
        if filename:
            self.ffmpeg_path_var.set(filename)
            self.refresh_audio_devices()

    def update_gui_status(self, status, color):
        self.status_var.set(status)
        self.status_dot.configure(text_color=color)

    def start_streaming(self):
        token = self.token_var.get().strip()
        channel_id_str = self.channel_id_var.get().strip()
        audio_device = self.device_combobox.get()
        mode = self.mode_var.get()
        ffmpeg_executable = self.ffmpeg_path_var.get().strip()
        target_win = self.window_combobox.get()
        
        if not token:
            messagebox.showerror("Campos Obrigatórios", "Por favor, insira o Token do Discord Bot na aba Configurações & Bot.")
            self.tabview.set("⚙️ Configurações & Bot")
            return

        channel_id = None
        if channel_id_str:
            try:
                channel_id = int(channel_id_str)
            except ValueError:
                messagebox.showerror("Valor Inválido", "O ID do canal de voz deve ser composto apenas por números.")
                return

        save_env_var("DISCORD_TOKEN", token)
        if channel_id_str:
            save_env_var("DISCORD_CHANNEL_ID", channel_id_str)
        save_env_var("FFMPEG_PATH", ffmpeg_executable)

        # Bloqueia a UI durante conexão
        self.start_button.configure(state="disabled")
        self.token_entry.configure(state="disabled")
        self.channel_entry.configure(state="disabled")
        self.device_combobox.configure(state="disabled")
        self.mode_combobox.configure(state="disabled")
        self.ffmpeg_entry.configure(state="disabled")
        self.window_combobox.configure(state="disabled")
        
        self.update_gui_status("Conectando...", "#f0b232")

        asyncio.run_coroutine_threadsafe(
            self.async_start_stream(token, channel_id, audio_device, mode, ffmpeg_executable, target_win=target_win), 
            self.bot_loop
        )

    def stop_streaming(self):
        self.stop_button.configure(state="disabled")
        self.update_gui_status("Desconectando...", "#f0b232")
        asyncio.run_coroutine_threadsafe(self.async_stop_stream(), self.bot_loop)

    # --- LÓGICA ASSÍNCRONA DO BOT ---
    async def async_start_stream(self, token, channel_id, audio_device, mode, ffmpeg_bin, target_channel=None, target_win=""):
        if self.bot.is_closed():
            self.bot = create_discord_bot(get_current_app)

        if not self.bot.is_ready():
            try:
                print("Iniciando conexão do bot com o Discord Gateway...")
                asyncio.create_task(self.bot.start(token))
                
                for _ in range(30):
                    if self.bot.is_ready():
                        break
                    await asyncio.sleep(0.5)
                    
                if not self.bot.is_ready():
                    self.after(0, self.on_connection_failed, "O bot não conseguiu se conectar ao Discord. Verifique se o Token é válido.")
                    return
            except Exception as e:
                self.after(0, self.on_connection_failed, f"Erro ao logar bot no Discord: {e}")
                return

        self.after(0, self.on_bot_turned_on)

        try:
            channel = target_channel
            if not channel and channel_id:
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    channel = await self.bot.fetch_channel(channel_id)
            
            if not channel:
                for guild in self.bot.guilds:
                    for vc in guild.voice_channels:
                        if len(vc.members) > 0:
                            channel = vc
                            break
                    if channel:
                        break

            if not channel or not isinstance(channel, discord.VoiceChannel):
                self.after(
                    0, 
                    self.on_connection_failed, 
                    "Nenhum canal de voz ativo foi encontrado.\n\n👉 Entre em um canal de voz no Discord e digite !start no chat, ou informe o ID do canal na aba Configurações & Bot."
                )
                return

            if self.voice_client and self.voice_client.is_connected():
                if self.voice_client.is_playing():
                    self.voice_client.stop()
                await self.voice_client.disconnect()

            print(f"Conectando ao canal de voz: {channel.name} (ID: {channel.id})...")
            self.voice_client = await channel.connect(timeout=20.0, reconnect=True)
            
            if "Nativo" in mode:
                print(f"Iniciando áudio no Modo NATIVO (SoundDevice) com o dispositivo: {audio_device}")
                self.current_stream = SoundDeviceAudioSource(device_name=audio_device)
            else:
                before_args = "-f dshow"
                input_source = f"audio={audio_device}"
                ffmpeg_options = "-vn -filter:a volume=1.0 -loglevel warning"
                print(f"Iniciando áudio no Modo FFMPEG com o dispositivo: {audio_device}")
                self.current_stream = discord.FFmpegPCMAudio(
                    source=input_source,
                    before_options=before_args,
                    options=ffmpeg_options,
                    executable=ffmpeg_bin
                )
            
            self.voice_client.play(self.current_stream)
            
            try:
                activity = discord.Streaming(
                    name=f"Áudio em Tempo Real ({channel.name})",
                    url="https://www.twitch.tv/discord"
                )
                asyncio.create_task(self.bot.change_presence(status=discord.Status.online, activity=activity))
                asyncio.create_task(channel.send(f"🟢 **Bot Ativado e Transmitindo!**\n🔊 Transmissão de áudio iniciada no canal de voz **{channel.name}**.\nDigite `!stop` no chat para encerrar."))
            except Exception as e:
                print(f"Aviso ao atualizar presença/mensagem: {e}")

            app_tag = target_win.split("(")[-1].replace(")", "").strip() if "(" in target_win else target_win[:20]
            status_desc = f"Transmitindo ({app_tag} ➔ {channel.name})" if app_tag else f"Transmitindo ({channel.name})"
            
            self.after(0, self.on_stream_started, status_desc)
            
        except discord.errors.Forbidden:
            self.after(0, self.on_connection_failed, f"O bot não possui permissão para conectar ou falar no canal de voz '{channel.name if 'channel' in locals() and channel else 'desconhecido'}'.")
        except Exception as e:
            self.after(0, self.on_connection_failed, f"Erro na conexão de áudio: {e}")

    async def async_stop_stream(self):
        try:
            if self.voice_client and self.voice_client.is_connected():
                if self.voice_client.is_playing():
                    self.voice_client.stop()
                await self.voice_client.disconnect()
        except Exception as e:
            print(f"Erro ao desconectar bot de voz: {e}")
        finally:
            self.voice_client = None
            self.current_stream = None
            self.after(0, self.on_stream_stopped)

    def on_stream_started(self, status_txt="Transmitindo"):
        self.update_gui_status(status_txt, "#23a55a")
        self.stop_button.configure(state="normal")

    def on_stream_stopped(self):
        self.update_gui_status("Bot Ligado (Pronto para !start)", "#23a55a")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
        self.token_entry.configure(state="normal")
        self.channel_entry.configure(state="normal")
        self.device_combobox.configure(state="normal")
        self.mode_combobox.configure(state="normal")
        self.ffmpeg_entry.configure(state="normal")
        self.window_combobox.configure(state="normal")

    def on_connection_failed(self, error_message):
        messagebox.showerror("Falha na Transmissão", error_message)
        self.on_stream_stopped()

    def on_closing(self):
        if self.voice_client and self.voice_client.is_connected():
            if messagebox.askokcancel("Sair", "Você está transmitindo no momento. Deseja fechar e parar a transmissão?"):
                future = asyncio.run_coroutine_threadsafe(self.async_stop_stream(), self.bot_loop)
                try:
                    future.result(timeout=3.0)
                except Exception:
                    pass
            else:
                return
                
        if self.bot and not self.bot.is_closed():
            future = asyncio.run_coroutine_threadsafe(self.bot.close(), self.bot_loop)
            try:
                future.result(timeout=3.0)
            except Exception:
                pass
                
        self.bot_loop.call_soon_threadsafe(self.bot_loop.stop)
        self.destroy()
        sys.exit(0)
