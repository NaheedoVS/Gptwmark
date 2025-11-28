# bot.py — Fully working on Heroku with aiogram 3.x (2025 version)

import os
import tempfile
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import aiohttp
from watermark import add_watermark


BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set!")

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Per-user queue
user_queues = {}


async def download_file(file_path: str) -> str:
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                os.unlink(tmp_file.name)
                raise RuntimeError(f"Download failed: HTTP {resp.status}")
            with open(tmp_file.name, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 1024):
                    f.write(chunk)
    return tmp_file.name


async def process_video(message: Message, input_path: str):
    output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    status = await message.reply("Adding watermark...")

    success = add_watermark(
        input_path=input_path,
        output_path=output_file.name,
        text="Your Watermark",
        color="white",
        font_size=36
    )

    # Clean input file early
    try:
        os.unlink(input_path)
    except:
        pass

    if not success:
        await status.edit_text("Failed to add watermark")
        try:
            os.unlink(output_file.name)
        except:
            pass
        return

    await status.edit_text("Uploading your watermarked video...")

    try:
        await message.answer_video(
            video=FSInputFile(output_file.name),
            caption="Here’s your watermarked video!",
            supports_streaming=True
        )
        await status.delete()
    except Exception as e:
        await status.edit_text(f"Upload error: {e}")
    finally:
        try:
            os.unlink(output_file.name)
        except:
            pass


async def handle_queue(user_id: int):
    while user_id in user_queues and user_queues[user_id]:
        message, video_path = user_queues[user_id].pop(0)
        try:
            await process_video(message, video_path)
        except Exception as e:
            await message.answer(f"Error: {e}")
    user_queues.pop(user_id, None)


@dp.message(F.video)
async def video_handler(message: Message):
    user_id = message.from_user.id
    status = await message.reply("Downloading video...")

    try:
        file = await bot.get_file(message.video.file_id)
        input_path = await download_file(file.file_path)
        await status.edit_text("Download complete! Adding watermark...")
    except Exception as e:
        await status.edit_text(f"Download failed: {e}")
        return

    if user_id not in user_queues:
        user_queues[user_id] = []

    user_queues[user_id].append((message, input_path))

    if len(user_queues[user_id]) == 1:
        asyncio.create_task(handle_queue(user_id))


async def main():
    print("Watermark Bot is starting... (aiogram 3.x)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
