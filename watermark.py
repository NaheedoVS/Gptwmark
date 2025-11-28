# watermark.py
import ffmpeg
import os

def add_watermark(input_path: str, output_path: str, text: str = "Your Watermark", 
                  color: str = "white", font_size: int = 36) -> bool:
    try:
        if not os.path.exists(input_path):
            return False

        # Проверяем, есть ли аудио — если нет, отключаем его в выходном файле
        probe = ffmpeg.probe(input_path)
        has_audio = any(stream['codec_type'] == 'audio' for stream in probe['streams'])

        stream = ffmpeg.input(input_path)

        # Текст в правом нижнем углу
        video = stream.video.filter(
            'drawtext',
            text=text,
            fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # точно есть в buildpack
            fontsize=font_size,
            fontcolor=color,
            x='w-tw-10',
            y='h-th-10',
            shadowx=2,
            shadowy=2,
            shadowcolor='black@0.5',
            escape_text=False
        )

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
