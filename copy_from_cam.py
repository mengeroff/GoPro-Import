import os
import re
import PIL.Image
import datetime
import logging

cam_path = "Q:/DCIM"

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
                logging.warning("unknown file format for file " + os.path.join(root, name))


def process_video_file(root, name):
    path = os.path.join(root, name)
    logging.info("video file: " + path)

    try:
        img = PIL.Image.open(path)
        exif_data = img._getexif()
        logging.debug(exif_data)
    except OSError:
        logging.info("Cannot identify video file " + path + ". Continuing.")


def process_photo_file(root, name):
    path = os.path.join(root, name)
    logging.info("photo file: " + path)

    try:
        img = PIL.Image.open(path)
        exif_data = img._getexif()
        logging.debug(exif_data)
    except OSError:
        logging.info("Cannot identify image file " + path + ". Continuing.")


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
    start_time = datetime.datetime.now()

    logging.basicConfig(
        filename="logs/" + start_time.strftime("%Y-%m-%d-%H%M%S") + '_gopro_import.log',
        level=logging.INFO,
        format='%(levelname)s:%(message)s'
    )

    logging.info("  ___  __ ____ ____  __     __ _  _ ____  __ ____ ____ ")
    logging.info(" / __)/  (  _ (  _ \/  \ __(  | \/ |  _ \/  (  _ (_  _)")
    logging.info("( (_ (  O ) __/)   (  O |___)(/ \/ \) __(  O )   / )(  ")
    logging.info(" \___/\__(__) (__\_)\__/   (__)_)(_(__)  \__(__\_)(__) ")
    logging.info("")
    logging.info("Start Time: " + str(start_time))

    main()

    end_time = datetime.datetime.now()
    logging.info("End Time: " + str(end_time))
    duration = end_time - start_time
    logging.info("Duration: " + str(duration))
