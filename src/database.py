import os
import sqlite3

DB_FILE = os.path.join(os.getcwd(), "vanilla_local.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa as tabelas do banco de dados local SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela 1: Fichas de Inimigos / Criaturas RPG
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enemy_sheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT DEFAULT 'global',
            name TEXT NOT NULL,
            name_lower TEXT NOT NULL UNIQUE,
            current_hp INTEGER NOT NULL,
            max_hp INTEGER NOT NULL,
            ac TEXT DEFAULT 'N/A',
            status TEXT DEFAULT 'Alive'
        )
    """)

    # Tabela 2: Economia e Sistema de Níveis
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_economy (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 100,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            last_msg_time REAL DEFAULT 0,
            last_daily REAL DEFAULT 0
        )
    """)

    # Tabela 3: Configurações de Servidor (Boas-Vindas / Despedidas)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_settings (
            guild_id TEXT PRIMARY KEY,
            welcome_channel_id TEXT DEFAULT '',
            goodbye_channel_id TEXT DEFAULT '',
            welcome_msg TEXT DEFAULT '🎉 Seja muito bem-vindo(a) ao {server}, {user}! Agora somos {member_count} membros!',
            goodbye_msg TEXT DEFAULT '👋 {user.name} saiu do servidor {server}. Agora somos {member_count} membros.',
            welcome_image_url TEXT DEFAULT '',
            goodbye_image_url TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()

# Inicializa ao importar
init_db()
