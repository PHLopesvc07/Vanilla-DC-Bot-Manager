import os
import sys
import shutil
import win32com.client
import tkinter as tk
from tkinter import messagebox, ttk

APP_NAME = 'Vanilla DC Bot Manager'
EXE_NAME = 'DiscordSimpleBotClient.exe'

def get_desktop_path():
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    if not os.path.exists(desktop):
        desktop = os.path.join(os.path.expanduser('~'), 'Área de Trabalho')
    return desktop

def create_shortcut(target_exe, shortcut_path, working_dir, description):
    shell = win32com.client.Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_exe
    shortcut.WorkingDirectory = working_dir
    shortcut.Description = description
    shortcut.save()

def install():
    try:
        app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        install_dir = os.path.join(app_data, 'VanillaDCBotManager')
        
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        source_dir = os.path.join(base_path, 'DiscordSimpleBotClient')
        if not os.path.exists(source_dir):
            source_dir = os.path.join(base_path, 'dist', 'DiscordSimpleBotClient')
        if not os.path.exists(source_dir):
            source_dir = os.path.join(os.getcwd(), 'dist', 'DiscordSimpleBotClient')

        if not os.path.exists(source_dir):
            messagebox.showerror('Erro de Instalação', f'Arquivos da aplicação não encontrados em:\n{source_dir}')
            return

        lbl_status.config(text='Copiando arquivos da aplicação...')
        root.update()

        if os.path.exists(install_dir):
            shutil.rmtree(install_dir, ignore_errors=True)

        shutil.copytree(source_dir, install_dir)

        lbl_status.config(text='Criando atalho na Área de Trabalho...')
        root.update()

        target_exe = os.path.join(install_dir, EXE_NAME)
        desktop_dir = get_desktop_path()
        shortcut_path = os.path.join(desktop_dir, f'{APP_NAME}.lnk')

        create_shortcut(
            target_exe=target_exe,
            shortcut_path=shortcut_path,
            working_dir=install_dir,
            description='Gerenciador e Cliente de Bot do Discord Vanilla'
        )

        progress.stop()
        progress['value'] = 100
        lbl_status.config(text='Instalação concluída com sucesso!')
        messagebox.showinfo('Sucesso!', f'{APP_NAME} foi instalado com sucesso!\n\nAtalho criado na Área de Trabalho:\n{shortcut_path}')
        root.destroy()

    except Exception as e:
        messagebox.showerror('Erro ao Instalar', f'Ocorreu um erro durante a instalação:\n{e}')
        lbl_status.config(text='Falha na instalação.')

root = tk.Tk()
root.title(f'Instalador - {APP_NAME}')
root.geometry('480x220')
root.resizable(False, False)

root.update_idletasks()
width = root.winfo_width()
height = root.winfo_height()
x = (root.winfo_screenwidth() // 2) - (width // 2)
y = (root.winfo_screenheight() // 2) - (height // 2)
root.geometry(f'{width}x{height}+{x}+{y}')

frame = ttk.Frame(root, padding='20')
frame.pack(fill='both', expand=True)

lbl_title = ttk.Label(frame, text=f'Assistente de Instalação: {APP_NAME}', font=('Segoe UI', 12, 'bold'))
lbl_title.pack(anchor='w', pady=(0, 10))

lbl_info = ttk.Label(frame, text='Este assistente instalará o Vanilla DC Bot Manager no seu computador e criará um atalho direto na sua Área de Trabalho.', wraplength=420)
lbl_info.pack(anchor='w', pady=(0, 15))

progress = ttk.Progressbar(frame, mode='indeterminate')
progress.pack(fill='x', pady=(0, 10))
progress.start(10)

lbl_status = ttk.Label(frame, text='Pronto para instalar.', font=('Segoe UI', 9, 'italic'))
lbl_status.pack(anchor='w', pady=(0, 15))

btn_install = ttk.Button(frame, text='🚀 Instalar Agora', command=install)
btn_install.pack(side='right')

root.mainloop()
