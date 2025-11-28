import os
import logging
import asyncio
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from telegram.request import HTTPXRequest

from config import Config
from storage import db
import watermark

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Video Watermark Bot**\n\n"
        "Send a video (Max 2GB) to start.\n"
        "Commands:\n"
        "/setwatermark <text> - Change text\n"
        "/setcolor - Change watermark color 🎨",
        parse_mode="Markdown"
    )


async def set_watermark_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /setwatermark <text>")
        return
    text = " ".join(context.args)
    db.set_watermark(user_id, text)
    await update.message.reply_text(f"✅ Watermark set: `{text}`", parse_mode="Markdown")


async def set_color_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    for color_name in Config.COLORS.keys():
        row.append(
            InlineKeyboardButton(f"🎨 {color_name}", callback_data=f"color:{color_name}")
        )
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row: keyboard.append(row)

    await update.message.reply_text(
        "🎨 **Choose a color for your watermark:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("color:"):
        color = data.split(":")[1]
        user_id = query.from_user.id
        db.set_color(user_id, color)

        await query.edit_message_text(
            f"✅ Watermark color updated to **{color}**",
            parse_mode="Markdown"
        )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user_id = update.effective_user.id

    file_obj = None

    if msg.video:
        file_obj = msg.video
    elif msg.document and "video" in msg.document.mime_type:
        file_obj = msg.document
    else:
        return

    status = await msg.reply_text("⏳ Fetching video…")

    # Get direct Telegram streaming URL
    file_info = await context.bot.get_file(file_obj.file_id)
    file_url = file_info.file_path

    user_text = db.get_watermark(user_id)
    color_name = db.get_color(user_id)
    color_rgb = Config.COLORS.get(color_name, (255, 255, 255))

    await status.edit_text("⚙️ Creating watermark…")

    with tempfile.TemporaryDirectory() as temp_dir:
        wm_path = os.path.join(temp_dir, "wm.png")
        await asyncio.to_thread(watermark.create_text_watermark, user_text, wm_path, color_rgb)

        out_dir = os.path.join(temp_dir, "out")
        os.makedirs(out_dir, exist_ok=True)

        await status.edit_text("🎥 Processing video (Streaming mode)…")

        output_files = watermark.process_video_streaming(
            file_url=file_url,
            watermark_img=wm_path,
            output_dir=out_dir
        )

        await status.edit_text("⬆️ Uploading…")

        for idx, part in enumerate(output_files, start=1):
            caption = f"Watermarked ({color_name})"
            if len(output_files) > 1:
                caption = f"Part {idx}/{len(output_files)} ({color_name})"

            with open(part, "rb") as vid:
                await msg.reply_video(video=vid, caption=caption)

    await status.delete()


def main():
    request = HTTPXRequest(
        connect_timeout=60,
        read_timeout=3600,
        write_timeout=3600
    )

    app = (
        ApplicationBuilder()
        .token(Config.BOT_TOKEN)
        .request(request)
        .get_updates_http_version("1.1")
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setwatermark", set_watermark_command))
    app.add_handler(CommandHandler("setcolor", set_color_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))

    app.run_polling()


if __name__ == "__main__":
    main()
  
