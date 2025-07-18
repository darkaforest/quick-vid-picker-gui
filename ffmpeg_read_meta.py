import subprocess
import json


def get_video_metadata(file_path):
    command = [
        'ffprobe',
        '-v', 'error',
        '-hide_banner',
        '-show_format',
        '-show_streams',
        '-of', 'json',
        file_path
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            text=True
        )
        metadata = json.loads(result.stdout)
        return metadata

    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: ffprobe not found. Make sure FFmpeg is installed.")
        return None

def get_video_duration(metadata):
    duration = 0
    for stream in metadata.get("streams", []):
        if stream.get("codec_type") == "video":
            duration_value = stream.get("duration")
            if duration_value is not None:
                try:
                    duration = float(duration_value)
                    break  # Found valid duration, exit loop
                except ValueError:
                    # Handle case where duration exists but isn't a valid number
                    print(f"Warning: Invalid duration value '{duration_value}' found in video stream")
    return duration

def get_video_resolution(metadata):
    for stream in metadata["streams"]:
        if stream["codec_type"] == "video":
            width = stream["coded_width"]
            height = stream["coded_height"]
    return width, height


# 使用示例
if __name__ == "__main__":
    video_path = "resources/input5.mkv"  # 替换为你的视频路径
    metadata = get_video_metadata(video_path)

    if metadata:
        print("Video Metadata:")
        print(json.dumps(metadata, indent=2))
        print("Video Duration: " + str(get_video_duration(metadata)))
        print(get_video_resolution(metadata))