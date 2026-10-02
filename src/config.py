import os
from dotenv import load_dotenv, set_key

def get_app_data_dir() -> str:
    """Retorna o diretório isolado de dados do usuário local para salvar configurações e banco de dados."""
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    app_dir = os.path.join(base, "VanillaDCBotManager")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

APP_DATA_DIR = get_app_data_dir()
ENV_FILE = os.path.join(APP_DATA_DIR, ".env")

# Cria o arquivo .env no APPDATA do usuário se não existir
if not os.path.exists(ENV_FILE):
    with open(ENV_FILE, "w", encoding="utf-8") as f:
        f.write("DISCORD_TOKEN=''\n")

load_dotenv(ENV_FILE)

def get_env_var(key: str, default: str = "") -> str:
    load_dotenv(ENV_FILE, override=True)
    return os.getenv(key, default).strip()

def save_env_var(key: str, value: str):
    try:
        set_key(ENV_FILE, key, value)
        os.environ[key] = value
    except Exception as e:
        print(f"Erro ao salvar {key} no .env: {e}")
