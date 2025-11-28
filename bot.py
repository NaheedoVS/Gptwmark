import os
import tempfile
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.utils import executor
import aiohttp
from watermark import add_watermark  # Make sure this function works with your video files


BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Simple per-user queue to process multiple videos one by one
user_queues = {}


async def download_file(file_path: str) -> str:
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(download_url) as resp:
            if resp.status == 200:
                with open(tmp_file.name, "wb") as f:
                    f.write(await resp.read())
            else:
                os.unlink(tmp_file.name)
                raise RuntimeError(f"Failed to download video, status: {resp.status}")
    
    return tmp_file.name


async def process_video(message: types.Message, input_path: str):
    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    status = await message.reply("Adding watermark...")

    success = add_watermark(
        input_path,
        tmp_out.name,
        text="Your Watermark",
        color="white",
        font_size=24
    )

    if not success:
        await status.edit_text("Watermark failed")
        # Clean up
        for path in [input_path, tmp_out.name]:
            try:
                os.unlink(path)
            except:
                pass
        return

    await status.edit_text("Watermark added. Uploading video...")
    
    try:
        await message.reply_video(
            video=FSInputFile(tmp_out.name),
            supports_streaming=True,
            caption="Here’s your water
