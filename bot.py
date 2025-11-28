import os
import tempfile
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.utils import executor
import aiohttp
from watermark import add_watermark

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Simple per-user queue to process multiple videos one by one

user_queues = {}

async def download_file(file_path):
tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
download_url = f"[https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}](https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path})"
async with aiohttp.ClientSession() as session:
    async with session.get(download_url) as resp:
        if resp.status == 200:
            with open(tmp_file.name, "wb") as f:
                f.write(await resp.read())
else:
raise RuntimeError("Failed to download video")
return tmp_file.name

async def process_video(message: types.Message, input_path: str):
tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
status = await message.reply("🔧 Adding watermark...")

```
success = add_watermark(
    input_path,
    tmp_out.name,
    text="Your Watermark",
    color="white",
    font_size=24
)
if not success:
    await status.edit_text("❌ Watermark failed")
    os.unlink(input_path)
    return

await status.edit_text("✅ Watermark added. Uploading video...")
await message.reply_video(FSInputFile(tmp_out.name), supports_streaming=True, caption="Here’s your watermarked video!")

# Clean temp files
try: os.unlink(input_path)
except: pass
try: os.unlink(tmp_out.name)
except: pass
```

async def handle_queue(user_id: int):
"""Processes queued videos one by one"""
queue = user_queues.get(user_id, [])
while queue:
message, file_path = queue.pop(0)
try:
await process_video(message, file_path)
except Exception as e:
await message.reply(f"❌ Error processing video: {e}")
user_queues.pop(user_id, None)  # Remove queue when done

@dp.message_handler(content_types=types.ContentType.VIDEO)
async def handle_video(message: types.Message):
user_id = message.from_user.id
await message.reply("🌐 Downloading video...")
file = await bot.get_file(message.video.file_id)

```
try:
    input_path = await download_file(file.file_path)
except Exception as e:
    await message.reply(f"❌ Failed to download: {e}")
    return

# Add to user queue
if user_id not in user_queues:
    user_queues[user_id] = []
user_queues[user_id].append((message, input_path))

# If queue length is 1, start processing immediately
if len(user_queues[user_id]) == 1:
    asyncio.create_task(handle_queue(user_id))
```

if **name** == "**main**":
executor.start_polling(dp, skip_updates=True)
