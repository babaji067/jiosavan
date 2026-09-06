import os
import aiofiles
import aiohttp
from PIL import Image

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)


async def download_thumbnail(videoid: str):
    """
    YouTube ka direct thumbnail download karta hai.
    """
    output = f"{CACHE_DIR}/{videoid}_thumb.jpg"

    if os.path.exists(output):
        return output

    urls = [
        f"https://i.ytimg.com/vi/{videoid}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{videoid}/hqdefault.jpg",
    ]

    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()

                        async with aiofiles.open(output, "wb") as f:
                            await f.write(data)

                        return output

            except Exception:
                continue

    return None


async def gen_thumb(videoid: str, player_username=None):
    """
    Sirf normal YouTube thumbnail.
    No box, no border, no text, no overlay.
    """

    path = f"{CACHE_DIR}/{videoid}_final.jpg"

    if os.path.exists(path):
        return path

    thumb_path = await download_thumbnail(videoid)

    if not thumb_path:
        return None

    try:
        image = Image.open(thumb_path).convert("RGB")

        # 16:9 ratio
        target_ratio = 16 / 9

        width, height = image.size
        current_ratio = width / height

        if current_ratio > target_ratio:
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2

            image = image.crop(
                (left, 0, left + new_width, height)
            )

        elif current_ratio < target_ratio:
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2

            image = image.crop(
                (0, top, width, top + new_height)
            )

        # Final size
        image = image.resize(
            (1280, 720),
            Image.Resampling.LANCZOS
        )

        image.save(
            path,
            "JPEG",
            quality=95,
            optimize=True
        )

        return path

    except Exception as e:
        print(f"Thumbnail Error: {e}")
        return None


async def get_thumb(videoid: str, user_id=None):
    return await gen_thumb(videoid)
    
