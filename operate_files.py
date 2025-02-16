import os
import shutil

def copy_file(src, dst):
    shutil.copy2(os.path.abspath(src), os.path.abspath(dst))

def delete_file(path):
    target = os.path.abspath(path)
    if os.path.isdir(target):
        shutil.rmtree(target)
    else:
        os.remove(target)

if __name__ == "__main__":
    copy_file("resources/input.mp4", "resources/in2.mp4")
    delete_file("resources/output.jpg")