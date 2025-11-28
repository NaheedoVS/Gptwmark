import os
import subprocess

def add_watermark(input_path, output_path, text="Watermark", color="white", font_size=24):
    """
    Add centered text watermark to a video using FFmpeg.

    Args:
        input_path (str): path to input video
        output_path (str): path to output video
        text (str): watermark text
        color (str): 'white' or 'black'
        font_size (int): font size
    Returns:
        bool: True if video generated successfully
    """
    # Use DejaVuSans font bundled with FFmpeg on Heroku
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    if not os.path.exists(font_path):
        raise FileNotFoundError("Font file not found. Make sure DejaVuSans is installed.")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vf", f"drawtext=fontfile={font_path}:text='{text}':x=(w-text_w)/2:y=(h-text_h)/2:fontsize={font_size}:fontcolor={color}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        output_path
    ]

    process = subprocess.run(cmd, capture_output=True, text=True)

    if process.returncode != 0:
        print("FFmpeg failed:")
        print(process.stderr)
        return False

    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True
    else:
        print("Output file invalid")
        return False
        
