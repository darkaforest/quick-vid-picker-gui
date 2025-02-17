import subprocess
import json

from ffmpeg_read_meta import get_video_duration, get_video_metadata


# ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -i "input.mp4"
# ffmpeg -i "input.mp4" -vf "fps=16/141.456077,tile=4x4" -an "output.png"
def gen_preview_pic(file_path, output_path):
    command = [
        'ffmpeg',
        '-i', file_path,  # 输入文件
        '-vf', 'fps=16/' + str(get_video_duration(get_video_metadata(file_path))) + ',tile=4x4',  # 视频滤镜：帧率+平铺
        '-an',  # 禁用音频
        '-y',
        output_path
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            text=True
        )

    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: ffprobe not found. Make sure FFmpeg is installed.")
        return None


# 使用示例
if __name__ == "__main__":
    video_path = "resources/input.mp4"  # 替换为你的视频路径
    gen_preview_pic(video_path, "resources/preview.jpg")
