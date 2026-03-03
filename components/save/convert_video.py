import subprocess
import os


def convert_to_mp4(h264_file, delete_original=True):
    mp4_file = h264_file.replace(".h264", ".mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-framerate", "30", "-i", h264_file, "-c", "copy", mp4_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("Converted to:", mp4_file)
    if delete_original:
        os.remove(h264_file)
    return mp4_file
