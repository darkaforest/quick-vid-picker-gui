import sys
import os
import subprocess


def open_with_default_player(video_path):
    """
    使用系统默认播放器打开视频文件
    :param video_path: 视频文件路径（支持绝对路径和相对路径）
    """
    try:
        # 统一转换为绝对路径
        video_path = os.path.abspath(video_path)

        # 检查文件是否存在
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        # 根据操作系统选择打开方式
        if sys.platform == 'win32':
            # Windows系统
            os.startfile(video_path)

        elif sys.platform == 'darwin':
            # macOS系统
            subprocess.run(['open', video_path], check=True)

        else:
            # Linux及其他类Unix系统
            subprocess.run(['xdg-open', video_path], check=True)

        print(f"已使用默认播放器打开: {video_path}")

    except Exception as e:
        print(f"打开视频失败: {str(e)}")
        # 可根据需要添加更详细的错误处理


# 使用示例
if __name__ == "__main__":
    video_file = "resources/input.mp4"  # 替换为你的视频路径
    open_with_default_player(video_file)
