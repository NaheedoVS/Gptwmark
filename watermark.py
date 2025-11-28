# watermark.py
import ffmpeg
import os

def add_watermark(input_path: str, output_path: str, text: str = "Your Watermark", 
                  color: str = "white", font_size: int = 36) -> bool:
    try:
        if not os.path.exists(input_path):
            return False

        # NOTE: This simple filename relies on the FONTCONFIG_PATH environment variable 
        # being set to /app on Heroku to find the watermark_font.ttf file.
        FONT_FILENAME = 'watermark_font.ttf' 

        # Check for audio stream
        probe = ffmpeg.probe(input_path)
        has_audio = any(stream['codec_type'] == 'audio' for stream in probe['streams'])

        stream = ffmpeg.input(input_path)

        # Text watermark applied using the drawtext filter
        video = stream.video.filter(
            'drawtext',
            text=text,
            fontfile=FONT_FILENAME,  # Simple filename path
            fontsize=font_size,
            fontcolor=color,
            x='w-tw-10',
            y='h-th-10',
            shadowx=2,
            shadowy=2,
            shadowcolor='black@0.5',
            escape_text=False
        )
        
        # Determine output command based on presence of audio
        if has_audio:
            output = ffmpeg.output(stream.audio, video, output_path, 
                                 vcodec='libx264', acodec='aac', 
                                 preset='medium', crf=23)
        else:
            output = ffmpeg.output(video, output_path, 
                                 vcodec='libx264', preset='medium', crf=23)

        ffmpeg.run(output, overwrite_output=True, quiet=True)
        return True

    except ffmpeg.Error as e:
        print("FFmpeg error:", e.stderr.decode() if e.stderr else e)
        return False
    except Exception as e:
        print("Watermark error:", e)
        return False
