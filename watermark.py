import ffmpeg
import os
import logging
from PIL import Image, ImageDraw, ImageFont
from config import Config

logger = logging.getLogger(__name__)


def create_text_watermark(text: str, output_path: str, color_rgb: tuple):
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

        try:
            font = ImageFont.truetype(font_path, Config.FONT_SIZE)
        except:
            font = ImageFont.load_default()

        dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bbox = dummy_draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]

        img = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        final_color = color_rgb + (Config.OPACITY,)
        draw.text((15, 15), text, font=font, fill=final_color)

        img.save(output_path, "PNG")
        return True
    except Exception as e:
        logger.error(f"Watermark error: {e}")
        return False


def process_video_streaming(file_url: str, watermark_img: str, output_dir: str):
    try:
        output_pattern = os.path.join(output_dir, "part_%03d.mp4")

        (
            ffmpeg
            .input(file_url)
            .overlay(
                ffmpeg.input(watermark_img),
                x=f"main_w-overlay_w-{Config.MARGIN_X}",
                y=f"main_h-overlay_h-{Config.MARGIN_Y}"
            )
            .output(
                output_pattern,
                vcodec="libx264",
                preset="veryfast",
                crf=26,
                movflags="+faststart",
                f="segment",
                segment_time=1800,
                reset_timestamps=1
            )
            .run(capture_stdout=True, capture_stderr=True)
        )

        parts = [
            os.path.join(output_dir, f)
            for f in sorted(os.listdir(output_dir))
            if f.startswith("part_")
        ]

        return parts

    except ffmpeg.Error as e:
        logger.error(e.stderr.decode())
        return []
      
