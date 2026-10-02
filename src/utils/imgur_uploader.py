import os
import aiohttp
from src.config import get_env_var

class ImgurUploader:
    """Helper para upload anônimo de imagens e GIFs via Imgur API v3."""

    @staticmethod
    async def upload_image_bytes(image_bytes: bytes, filename: str = "image.png") -> str | None:
        client_id = get_env_var("IMGUR_CLIENT_ID", "546c25a59c58ad7")
        url = "https://api.imgur.com/3/image"
        
        headers = {
            "Authorization": f"Client-ID {client_id}"
        }
        
        form_data = aiohttp.FormData()
        form_data.add_field("image", image_bytes, filename=filename)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=form_data) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("data", {}).get("link")
                    else:
                        print(f"Erro no upload para o Imgur ({resp.status}): {await resp.text()}")
        except Exception as e:
            print(f"Exceção no upload para o Imgur: {e}")
            
        return None
