import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog,
    QVBoxLayout, QHBoxLayout, QListWidget, QPushButton,
    QLabel, QListWidgetItem, QFrame, QFormLayout
)
from PySide6.QtGui import QPixmap, QShortcut, QKeySequence
from PySide6.QtCore import Qt, QSize, QThread, Signal

from ffmpeg_gen_preview import gen_preview_pic
from play_video import open_with_default_player

v2p = dict()

# 新增工作线程类
class ProcessingThread(QThread):
    progress_updated = Signal(int, int, str)  # 当前进度，总数，文件名
    processing_finished = Signal()  # 新增完成信号

    def __init__(self, files):
        super().__init__()
        self.files = files

    def run(self):
        total = len(self.files)
        for idx, file_info in enumerate(self.files, 1):
            v = file_info["path"]
            p = "resources/" + file_info["name"].split(".")[0] + ".jpg"
            try:
                gen_preview_pic(v, p)
                v2p[v] = p
                self.progress_updated.emit(idx, total, file_info["name"])
            except Exception as e:
                error_msg = f"处理 {file_info['name']} 失���: {str(e)}"
                self.progress_updated.emit(idx, total, error_msg)
                print(error_msg)
        self.progress_updated.emit(0, 0, "")
        self.processing_finished.emit()  # 处理完成后发出信号

class FileItemWidget(QWidget):
    def hum_convert(self, value):
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        size = 1024.0
        for i in range(len(units)):
            if (value / size) < 1:
                return "%.2f%s" % (value, units[i])
            value = value / size

    def __init__(self, file_info):
        super().__init__()
        self.file_path = file_info["path"]

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"📄 {file_info['name']}"))
        layout.addWidget(QLabel(f"Size: {self.hum_convert(file_info['size'] * 1024)}"))
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.current_thread = None  # 新增实例变量
        self.current_file_path = None  # 新增当前文件路径存储
        self.valid_files = []  # 新增用于存储文件列表
        self.left_frame = None  # 新增左侧面板引用
        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()

        # ========== 左侧面板 ==========
        self.left_frame = QFrame()
        left_layout = QVBoxLayout(self.left_frame)  # 关键修改：直接为frame创建新布局

        self.folder_btn = QPushButton("选择文件夹")
        self.file_list = QListWidget()

        left_layout.addWidget(self.folder_btn)
        left_layout.addWidget(self.file_list)

        # ========== 中间面板 ==========
        center_frame = QFrame()
        self.center_label = QLabel()
        self.center_label.setAlignment(Qt.AlignCenter)
        center_layout = QVBoxLayout(center_frame)
        center_layout.addWidget(self.center_label)

        # ========== 右侧面板 ==========
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)  # 创建新布局

        # 元信息面板
        meta_frame = QFrame()
        meta_layout = QFormLayout(meta_frame)
        self.meta_name = QLabel()
        self.meta_size = QLabel()
        self.meta_time = QLabel()
        self.meta_name.setMaximumSize(QSize(100, 200))
        meta_layout.addRow("文件名:", self.meta_name)
        meta_layout.addRow("文件大小:", self.meta_size)
        meta_layout.addRow("修改时间:", self.meta_time)

        # 按钮面板
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        self.open_btn = QPushButton("打开")
        self.copy_btn = QPushButton("复制")
        self.del_btn = QPushButton("删除")
        self.open_btn.setFixedSize(QSize(100, 100))
        self.copy_btn.setFixedSize(QSize(100, 100))
        self.del_btn.setFixedSize(QSize(100, 100))
        self.del_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;  /* 红色背景 */
                color: black;              /* 黑色文字 */
                font-weight: bold;        /* 加粗字体 */
            }
            QPushButton:hover {
                background-color: #ff6666;  /* 悬停时稍亮的红色 */
            }
            QPushButton:pressed {
                background-color: #cc0000;  /* 按下时更深的红色 */
            }
        """)
        btn_layout.addWidget(self.open_btn)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.del_btn)
        left_layout.addWidget(btn_frame)

        # ========== 主布局 ==========
        main_layout.addWidget(self.left_frame, 1)
        main_layout.addWidget(center_frame, 5)
        main_layout.addWidget(right_frame, 2)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Signals
        self.folder_btn.clicked.connect(self.select_folder)
        self.file_list.currentItemChanged.connect(self.handle_item_changed)
        # 添加按钮点击信号连接
        self.open_btn.clicked.connect(self.on_open_clicked)
        self.copy_btn.clicked.connect(self.on_copy_clicked)
        self.del_btn.clicked.connect(self.on_delete_clicked)

        QApplication.instance().aboutToQuit.connect(self.cleanup_previews)  # 连接退出信号

        # 添加快捷键绑定（在方法末尾添加）
        # 打开文件 - 回车键（主键盘和小键盘）
        QShortcut(QKeySequence(Qt.Key_Return), self).activated.connect(self.on_open_clicked)
        QShortcut(QKeySequence(Qt.Key_Enter), self).activated.connect(self.on_open_clicked)

        # 删除文件 - Delete键和Backspace键
        QShortcut(QKeySequence(Qt.Key_Delete), self).activated.connect(self.on_delete_clicked)
        QShortcut(QKeySequence(Qt.Key_Backspace), self).activated.connect(self.on_delete_clicked)

    def handle_item_changed(self, current, previous):
        """处理当前选中项变化"""
        if current:
            self.show_file_info(current)
        else:
            self.center_label.clear()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            self.load_files(folder)

    def load_files(self, folder):
        self.file_list.clear()
        valid_files = self.prepare_valid_data(folder)
        self.valid_files = valid_files  # 存储文件列表
        self.left_frame.setEnabled(False)
        self.center_label.setText("正在加载文件...")
        # 创建并启动线程
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.terminate()

        self.current_thread = ProcessingThread(valid_files)
        self.current_thread.progress_updated.connect(self.update_processing_status)
        # 连接完成信号
        self.current_thread.processing_finished.connect(self.handle_processing_completed)
        self.current_thread.start()
        for fname in os.listdir(folder):
            path = os.path.join(folder, fname)
            is_valid, info = self.is_valid_video_file(path)
            if not is_valid or not info:
                continue
                item = QListWidgetItem()
                item.setSizeHint(QSize(200, 80))
                self.file_list.addItem(item)
                self.file_list.setItemWidget(item, FileItemWidget(info))

    # 新增状态更新方法
    def update_processing_status(self, current, total, name):
        self.center_label.setText(f'[{current}/{total}] processing {name}')
        if (current == 0 and total == 0):
            self.center_label.clear()

    def is_valid_video_file(self, file_path):
        """验证是否为有效的视频文件"""
        if not os.path.isfile(file_path):
            return False, None

        # 获取文件信息
        try:
            file_size = os.path.getsize(file_path) // 1024  # KB
            file_name = os.path.basename(file_path)
            file_ext = file_name.split(".")[-1].lower() if "." in file_name else ""

            # 检查文件扩展名和大小
            if file_ext not in ["mp4", "mkv", "mov", "avi", "ts", "flv", "f4v"]:
                return False, None
            if file_size <= 1024 * 1:  # 小于100MB
                return False, None

            # 返回文件信息
            return True, {
                "name": file_name,
                "size": file_size,
                "mtime": os.path.getmtime(file_path),
                "path": file_path
            }
        except Exception as e:
            print(f"验证文件 {file_path} 时出错: {str(e)}")
            return False, None

    def prepare_valid_data(self, folder):
        valid_files = []
        for fname in os.listdir(folder):
            path = os.path.join(folder, fname)
            is_valid, info = self.is_valid_video_file(path)
            if is_valid and info:
                valid_files.append(info)
        return valid_files
    def handle_processing_completed(self):
        """处理完成后的回调"""
        self.left_frame.setEnabled(True)
        if self.file_list.count() > 0:
            # 选中第一个项目
            first_item = self.file_list.item(0)
            self.file_list.setCurrentItem(first_item)

            # 手动触发选中事件
            self.show_file_info(first_item)

    def show_file_info(self, item):
        if isinstance(item, QListWidgetItem):
            file_widget = self.file_list.itemWidget(item)
            self.current_file_path = file_widget.file_path
            # 获取物理像素尺寸
            screen_ratio = self.devicePixelRatioF()
            label_width = int(self.center_label.width() * screen_ratio)
            label_height = int(self.center_label.height() * screen_ratio)

            # 使用高质量缩放
            pixmap = QPixmap(v2p[self.file_list.itemWidget(item).file_path])
            if not pixmap.isNull():
                # 保持宽高比缩放
                scaled_pixmap = pixmap.scaled(
                    label_width,
                    label_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation  # 使用高质量插值
                )
                # 设置设备像素比
                scaled_pixmap.setDevicePixelRatio(screen_ratio)
                self.center_label.setPixmap(scaled_pixmap)

    def on_open_clicked(self):
        open_with_default_player(self.current_file_path)

    def on_copy_clicked(self):
        if not self.current_file_path:
            return

        target_dir = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if target_dir:
            try:
                import shutil
                filename = os.path.basename(self.current_file_path)
                target_path = os.path.join(target_dir, filename)

                # 处理重名文件
                counter = 1
                while os.path.exists(target_path):
                    name, ext = os.path.splitext(filename)
                    target_path = os.path.join(target_dir, f"{name}({counter}){ext}")
                    counter += 1

                shutil.copy2(self.current_file_path, target_path)
                self.center_label.setText(f"文件已复制到：{target_path}")
            except Exception as e:
                self.center_label.setText(f"复制失败：{str(e)}")

    def on_delete_clicked(self):
        if not self.current_file_path:
            return

        try:
            current_row = self.file_list.currentRow()
            # 从文件系统删除
            os.remove(self.current_file_path)

            # 从列表删除
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                widget = self.file_list.itemWidget(item)
                if widget.file_path == self.current_file_path:
                    self.file_list.takeItem(i)
                    break

            self.center_label.setText("文件已删除")
            self.current_file_path = None
            # 手动设置新的选中项
            new_count = self.file_list.count()
            if new_count > 0:
                # 自动选择下一个有效项（优先选同一位置，超过长度选最后一个）
                new_row = min(current_row, new_count - 1)
                new_item = self.file_list.item(new_row)
                self.file_list.setCurrentItem(new_item)
                # 手动触发选中事件
                self.handle_item_changed(new_item, None)
            else:
                # 清空显示
                self.current_file_path = None
                self.center_label.clear()
                self.meta_name.clear()
                self.meta_size.clear()
                self.meta_time.clear()
        except Exception as e:
            self.center_label.setText(f"删除失败：{str(e)}")

    def cleanup_previews(self):
        """清理预览图目录"""
        preview_dir = "resources"
        if os.path.exists(preview_dir):
            try:
                # 删除目录内所有文件
                for filename in os.listdir(preview_dir):
                    file_path = os.path.join(preview_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        error_msg = f"删除 {file_path} 失败: {str(e)}"
                        print(error_msg)
                        if hasattr(self, 'center_label'):
                            self.center_label.setText(error_msg)
                success_msg = "预览图已清理"
                print(success_msg)
                if hasattr(self, 'center_label'):
                    self.center_label.setText(success_msg)
            except Exception as e:
                error_msg = f"清理预览目录失败: {str(e)}"
                print(error_msg)
                if hasattr(self, 'center_label'):
                    self.center_label.setText(error_msg)

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # 启用高DPI缩放
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)     # 使用高DPI像素图
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())