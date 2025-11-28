# bot.py
import os
import tempfile
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
import aiohttp
from watermark import add_watermark

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set!")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

user_queues = {}

async def download_file(file_path: str) -> str:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            r.raise_for_status()
            with open(tmp.name, "wb") as f:
                async for chunk in r.content.iter_chunked(1024*1024):
                    f.write(chunk)
    return tmp.name

async def process_video(message: Message, in_path: str):
    out_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    status = await message.reply("Adding watermark...")

    success = add_watermark(in_path, out_file.name, text="Your Watermark", font_size=42)

    try: os.unlink(in_path)
    except: pass

    if not success:
        await status.edit_text("Failed to add watermark")
        try: os.unlink(out_file.name)
        except: pass
        return

    await status.edit_text("Uploading...")
    await message.answer_video(
        video=FSInputFile(out_file.name),
        caption="Here’s your watermarked video!",
        supports_streaming=True
    )
    await status.delete()
    try: os.unlink(out_file.name)
    except: pass

async def handle_queue(user_id: int):
    while user_id in user_queues and user_queues[user_id]:
        msg, path = user_queues[user_id].pop(0)
        try:
            await process_video(msg, path)
        except Exception as e:
            await msg.answer(f"Error: {e}")
    user_queues.pop(user_id, None)

@dp.message(F.video)
async def on_video(message: Message):
    user_id = message.from_user.id
    status = await message.reply("Downloading...")

    try:
        file = await bot.get_file(message.video.file_id)
        path = await download_file(file.file_path)
        await status.edit_text("Processing...")
    except Exception as e:
        await status.edit_text(f"Download error: {e}")
        return

    user_queues.setdefault(user_id, []).append((message, path))
    if len(user_queues[user_id]) == 1:
        asyncio.create_task(handle_queue(user_id))

async def main():
    print("Watermark Bot STARTED (Heroku + real ffmpeg)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
