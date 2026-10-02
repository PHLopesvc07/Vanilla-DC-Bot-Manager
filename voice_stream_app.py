import os
import asyncio
import threading
from src.config import get_env_var
from src.core.bot import create_discord_bot
from src.ui.app import VoiceStreamApp, get_current_app


def start_discord_bot_loop(loop):
    asyncio.set_event_loop(loop)
    try:
        loop.run_forever()
    except Exception as e:
        print(f"Loop do Bot encerrado: {e}", flush=True)


if __name__ == "__main__":
    initial_token = get_env_var("DISCORD_TOKEN")
    
    discord_loop = asyncio.new_event_loop()
    
    t = threading.Thread(
        target=start_discord_bot_loop, 
        args=(discord_loop,), 
        daemon=True
    )
    t.start()
    
    bot = create_discord_bot(get_current_app)
    
    if initial_token:
        asyncio.run_coroutine_threadsafe(bot.start(initial_token), discord_loop)

    app = VoiceStreamApp(bot, discord_loop)
    app.mainloop()
