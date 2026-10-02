import customtkinter as ctk
from tkinter import messagebox, simpledialog
from src.modules.rpg import EnemyManager

def build_rpg_tab(parent_tab):
    """Constrói a visualização e controles da Categoria 🎲 RPG & Dados com Gestão Local SQLite."""
    container = ctk.CTkScrollableFrame(parent_tab, fg_color="transparent")
    container.pack(fill="both", expand=True)

    # Card 1: Gestor de Fichas de Inimigos no SQLite Local
    card_enemies = ctk.CTkFrame(container, corner_radius=10)
    card_enemies.pack(fill="x", pady=6)
    
    ctk.CTkLabel(card_enemies, text="🐉 GESTOR DE FICHAS DE INIMIGOS (BANCO DE DADOS LOCAL SQLITE)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#248046").pack(anchor="w", padx=15, pady=(10, 4))
    
    ctk.CTkLabel(card_enemies, text="Gerencie e visualize todas as fichas ativas salvas no seu banco de dados local:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=15, pady=(0, 6))

    # Lista de Inimigos em Caixa de Texto / Frame
    enemy_list_frame = ctk.CTkFrame(card_enemies, fg_color="#1e1f22", corner_radius=8)
    enemy_list_frame.pack(fill="x", padx=15, pady=(0, 8))

    enemy_text_box = ctk.CTkTextbox(enemy_list_frame, height=120, font=ctk.CTkFont(family="Consolas", size=11))
    enemy_text_box.pack(fill="both", expand=True, padx=8, pady=8)

    def refresh_enemy_display():
        enemy_text_box.delete("1.0", "end")
        enemies = EnemyManager.get_all_enemies()
        if not enemies:
            enemy_text_box.insert("end", "Nenhum inimigo cadastrado no banco de dados local.")
            return

        lines = []
        for e in enemies:
            bar = EnemyManager.generate_health_bar(e['current_hp'], e['max_hp'])
            lines.append(f"• {e['name']} (AC: {e['ac']}) | HP: {e['current_hp']}/{e['max_hp']} | Status: {e['status']}\n  {bar}")
        enemy_text_box.insert("end", "\n\n".join(lines))

    refresh_enemy_display()

    btn_row = ctk.CTkFrame(card_enemies, fg_color="transparent")
    btn_row.pack(fill="x", padx=15, pady=(0, 12))

    def on_add_enemy():
        dialog = ctk.CTkInputDialog(
            text="Digite o comando de criação:\nEx: !set {Enemy Sheet}Name: \"Goblin\"; HP: 30; AC: 13;",
            title="Nova Ficha de Inimigo"
        )
        inp = dialog.get_input()
        if inp:
            res = EnemyManager.create_or_update_enemy(inp)
            messagebox.showinfo("Ficha Atualizada", res)
            refresh_enemy_display()

    def on_delete_enemy():
        dialog = ctk.CTkInputDialog(text="Digite o nome do inimigo a remover:", title="Deletar Ficha")
        inp = dialog.get_input()
        if inp:
            res = EnemyManager.delete_enemy(inp)
            messagebox.showinfo("Resultado", res)
            refresh_enemy_display()

    ctk.CTkButton(
        btn_row, text="➕ Adicionar/Editar Ficha", fg_color="#248046", hover_color="#1a6535",
        command=on_add_enemy
    ).pack(side="left", expand=True, fill="x", padx=(0, 4))

    ctk.CTkButton(
        btn_row, text="🗑️ Deletar Ficha", fg_color="#da373c", hover_color="#a92b2f",
        command=on_delete_enemy
    ).pack(side="left", expand=True, fill="x", padx=4)

    ctk.CTkButton(
        btn_row, text="🔄 Atualizar Lista", fg_color="#4f545c", hover_color="#686d73",
        command=refresh_enemy_display
    ).pack(side="right", expand=True, fill="x", padx=(4, 0))

    # Card 2: Guia de Notações de Dados Rollem
    card_dice = ctk.CTkFrame(container, corner_radius=10)
    card_dice.pack(fill="x", pady=6)
    
    ctk.CTkLabel(card_dice, text="🎲 SINTAXE E COMANDOS DE DADOS (ROLLEM BOT)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#f0b232").pack(anchor="w", padx=15, pady=(10, 4))
    
    txt_dice = (
        "   🎲  XdY [comentário] ➔ 1d20 ataque de espada (dado DEVE estar no início!)\n"
        "   💥  XdY! / XdY!Z     ➔ Dados explosivos (1d4! ou 1d6!3)\n"
        "   📜  XdYns           ➔ No-sort (ordem exata do sorteio)\n"
        "   ➕  8d6++2 / 8d6--2 ➔ Soma/Subtrai valor a CADA um dos dados\n"
        "   🔢  ((8d6+3)*(7d4/2)) ➔ Ordem de parênteses e matemática completa\n"
        "   🎯  8d6<<3 / 8d6>>3 ➔ Conta quantos dados caíram <= ou >= que o valor\n"
        "   ☯️  dF / 4dF         ➔ Dados Fate/Fudge (-1, 0, +1)\n"
        "   🔁  6#4d6           ➔ Executa a rolagem 6 vezes\n"
        "   🗡️  4d6d1 / 8d6dh3  ➔ Abandona menor (d1) ou maior (dh3) dado\n"
    )
    ctk.CTkLabel(card_dice, text=txt_dice, font=ctk.CTkFont(size=11), justify="left", anchor="w").pack(anchor="w", padx=15, pady=(0, 12))
