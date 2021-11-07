import asyncio

from io import BytesIO
from PIL import Image, ImageFont, ImageDraw

from .cut_string import get_cut_str

font_file = './font/sarasa-mono-sc-semibold.ttf'
font = ImageFont.truetype(font_file, 22)


async def create_image(text: str, cut=64) -> bytes:
    return await asyncio.to_thread(_create, text, cut)


def _create(text: str, cut=64) -> bytes:
    cut_str = '\n'.join(get_cut_str(text, cut))
    textx, texty = font.getsize_multiline(cut_str)
    image = Image.new('RGB', (textx + 50, texty + 50), (242, 242, 242))
    draw = ImageDraw.Draw(image)
    draw.text((20, 20), cut_str, font=font, fill=(31, 31, 33))
    image.save(imageio := BytesIO(), format="JPEG", quality=90, subsampling=2, qtables="web_high")
    return imageio.getvalue()
