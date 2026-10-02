import os
from dotenv import load_dotenv, set_key

load_dotenv()
ENV_FILE = os.path.join(os.getcwd(), ".env")

def get_env_var(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()

def save_env_var(key: str, value: str):
    try:
        set_key(ENV_FILE, key, value)
    except Exception as e:
        print(f"Erro ao salvar {key} no .env: {e}")
