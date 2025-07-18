import subprocess
import json
import glob
import os

from ffmpeg_read_meta import get_video_duration, get_video_metadata, get_video_resolution


def create_time_segments(duration, segmentCount):
    if segmentCount <= 0:
        raise ValueError("segmentCount must be a positive integer")

    interval = duration / segmentCount
    times = [0]

    for i in range(1, segmentCount):
        current = i * interval
        if current > duration:
            current = duration
        times.append(int(current))

    return times


def gen_preview_pic(file_path, output_name):
    c = 1
    metadata = get_video_metadata(file_path)
    duration = get_video_duration(metadata)
    for i in create_time_segments(duration, 16):
        gen_preview_pic0(file_path, 'resources/seg_' + output_name + str(c) + ".jpg", i)
        c += 1
    run([
        'ffmpeg',
        '-hwaccel', 'auto',
        '-i', 'resources/seg_' + output_name + '%d.jpg',  # 输入文件
        '-filter_complex', 'tile=4x4',  # 视频滤镜：帧率+平铺
        '-vframes', '1',
        '-c:v', 'mjpeg',
        '-threads', 'auto',
        '-y',
        'resources/seg_' + output_name + ".jpg"
    ])
    run([
        'ffmpeg',
        '-hwaccel', 'auto',
        '-i', 'resources/seg_' + output_name + '.jpg',  # 输入文件
        '-vf', 'scale=3840:2160:flags=fast_bilinear',  # 视频滤镜：帧率+平铺
        '-q:v', '5',
        '-threads', 'auto',
        '-y',
        'resources/' + output_name + ".jpg"
    ])
    try:
        # 使用跨平台的方式删除文件
        for file_path in glob.glob('resources/seg_*'):
            if os.path.exists(file_path):
                os.remove(file_path)
        print("成功删除匹配文件。")
    except Exception as e:
        print(f"删除失败，错误信息：{e}")
    # ffmpeg -i preview%d.jpg -filter_complex tile=4x4 -vframes 1 output2.jpg
    # run([
    #     'rm'
    #     '-f', 'seg_' + output_name + '*'
    # ])
    # run([
    #     'rm -f'
    # ])
    # ffmpeg -i output2.jpg -vf scale=3840:2160 -q:v 10 output4.jpg


# ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -i "input.mp4"
# ffmpeg -i "input.mp4" -vf "fps=16/141.456077,tile=4x4" -an "output.png"
def gen_preview_pic0(file_path, output_path, ss):
    run([
        'ffmpeg',
        '-hwaccel', 'auto',
        '-ss', str(ss),  # 视频滤镜：帧率+平铺
        '-i', file_path,  # 输入文件
        '-vframes', '1',
        '-vsync', 'vfr',
        '-threads', 'auto',
        '-y',
        output_path
    ])
    # ffmpeg  -i input.mp4  -ss 4.500 -vframes 1 output.png

def run(command):
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
        print("Error: not found.")
        return None

# 使用示例
if __name__ == "__main__":
    video_path = "resources/input7.mp4"  # 替换为你的视频路径
    gen_preview_pic(video_path, "preview")