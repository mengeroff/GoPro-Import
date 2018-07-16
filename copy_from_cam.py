import os
import re
import PIL.Image

cam_path = "Q:\\DCIM"

video_file_ext = [r'.*.mp4', r'.*.thm', r'.*.lrv']
photo_file_ext = [r'.*.jpg', r'.*.gpr']


def main():
    for root, dirs, files in os.walk(cam_path, topdown=False):
        for name in files:
            if is_video_file(name):
                process_video_file(root, name)
            elif is_photo_file(name):
                process_photo_file(root, name)
            else:
                print("unknown file format for file " + os.path.join(root, name))


def process_video_file(root, name):
    path = os.path.join(root, name)
    print("video file: " + path)

    try:
        img = PIL.Image.open(path)
        exif_data = img._getexif()
        print(exif_data)
    except OSError:
        print("Cannot identify video file " + path + ". Continuing.")


def process_photo_file(root, name):
    path = os.path.join(root, name)
    print("photo file: " + path)

    try:
        img = PIL.Image.open(path)
        exif_data = img._getexif()
        print(exif_data)
    except OSError:
        print("Cannot identify image file " + path + ". Continuing.")


def is_video_file(name):
    for regex in video_file_ext:
        match_obj = re.match(regex, name.lower(), re.M | re.I)
        if match_obj:
            return True

    return False


def is_photo_file(name):
    for regex in photo_file_ext:
        match_obj = re.match(regex, name.lower(), re.M | re.I)
        if match_obj:
            return True

    return False


if __name__ == '__main__':
    main()
