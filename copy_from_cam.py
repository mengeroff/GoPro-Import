import os
import time
import sys
import re
import datetime
import logging
import argparse
from shutil import copyfile
import sqlite3

cam_path = ""
dest_path = ""
log_path = ""
log_level = "INFO"
db_path = ""
db_cursor = None
db_conn = None

video_file_ext = [r'.*.mp4', r'.*.thm', r'.*.lrv']
photo_file_ext = [r'.*.jpg', r'.*.gpr']

total_processed_videos = 0
total_processed_pics = 0
total_warnings = 0


def parse_arguments():
    global cam_path
    global dest_path
    global log_path
    global log_level
    global db_path

    parser = argparse.ArgumentParser()
    parser.add_argument("cam_path", help="The path to your GoPro.")
    parser.add_argument("dest_path", help="The path where you want to keep your GoPro files.")
    parser.add_argument("--log", help="Setting of the log level. Possible values are 'DEBUG', 'INFO', 'WARNING', 'ERROR', and 'CRITICAL'")
    args = parser.parse_args()
    cam_path = args.cam_path
    dest_path = args.dest_path
    log_path = dest_path + "logs/"
    db_path = log_path + "file_log.sqlite"
    if args.log:
        log_level = args.log


def main():
    global cam_path
    global total_warnings
    global total_processed_videos
    global total_processed_pics

    # get the total amount of files to handle
    total_files = 0

    for root, dirs, files in os.walk(cam_path, topdown=False):
        for file in files:
            total_files += 1

    # process each file
    progress_iter = 0
    for root, dirs, files in os.walk(cam_path, topdown=False):
        for name in files:
            if is_video_file(name):
                process_general_file(root, name)
                total_processed_videos += 1
            elif is_photo_file(name):
                process_general_file(root, name)
                total_processed_pics += 1
            else:
                if not re.match(r'.*.sav', name.lower(), re.M | re.I):
                    logging.warning("unknown file format for file " + os.path.join(root, name))
                    total_warnings += 1

            progress_iter += 1
            print_progress(progress_iter, total_files, prefix='Progress:')


def process_general_file(root, name):
    global db_cursor
    global db_conn

    path = os.path.join(root, name)
    logging.debug("file: " + path)

    date_created = datetime.datetime.strptime(time.ctime(os.path.getctime(path)), "%a %b %d %H:%M:%S %Y")
    date_created = date_created.strftime("%Y-%m-%d")

    # create folder with date
    directory = dest_path + str(date_created)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # check if file has already been copied
    db_cursor.execute("SELECT EXISTS(SELECT 1 FROM files WHERE file_name = ? AND date_created = ?)", (name, date_created,))
    data = db_cursor.fetchall()
    if data[0][0] == 0:
        # copy file
        dest = directory + "/" + name
        logging.info("Copying file from %s to %s" % (path, dest))
        copyfile(path, dest)

        # get file size
        file_size_bytes = os.path.getsize(path)
        file_size_mb = file_size_bytes / 1000000

        # add line to DB
        db_cursor.execute("INSERT INTO files VALUES ('%s','%s', '%s', %s)"
                          % (name, date_created, datetime.datetime.now().strftime("%Y-%m-%d"), file_size_mb))
        db_conn.commit()
    else:
        logging.info("File %s already exists in destination %s. Skipping." % (path, directory))


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


def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=100):
    """
    Call in a loop to create terminal progress bar

    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        bar_length  - Optional  : character length of bar (Int)
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


def prepare_db():
    global db_conn, db_cursor
    db_conn = sqlite3.connect(db_path)
    db_cursor = db_conn.cursor()
    # Create table
    db_cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (file_name text, date_created text, date_copied text, size real)""")


def print_header():
    logging.info("  ___  __ ____ ____  __     __ _  _ ____  __ ____ ____ ")
    logging.info(" / __)/  (  _ (  _ \/  \ __(  | \/ |  _ \/  (  _ (_  _)")
    logging.info("( (_ (  O ) __/)   (  O |___)(/ \/ \) __(  O )   / )(  ")
    logging.info(" \___/\__(__) (__\_)\__/   (__)_)(_(__)  \__(__\_)(__) \n\n")

    print("-------------------------------------------------------")
    print("  ___  __ ____ ____  __     __ _  _ ____  __ ____ ____ ")
    print(" / __)/  (  _ (  _ \/  \ __(  | \/ |  _ \/  (  _ (_  _)")
    print("( (_ (  O ) __/)   (  O |___)(/ \/ \) __(  O )   / )(  ")
    print(" \___/\__(__) (__\_)\__/   (__)_)(_(__)  \__(__\_)(__) ")
    print("-------------------------------------------------------\n\n")


def prepare_logging():
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % log_level)
    logging.basicConfig(
        filename=log_path + start_time.strftime("%Y-%m-%d-%H%M%S") + '_gopro_import.log',
        level=numeric_level,
        format='%(levelname)s:%(message)s'
    )
    getattr(logging, log_level.upper())


if __name__ == '__main__':
    # first off get the current time as the starting time
    start_time = datetime.datetime.now()

    # parse the arguments
    parse_arguments()

    # prepare the logging environment
    prepare_logging()

    # print the header to the log file and the console. We want to see what we're dealing with.
    print_header()

    # get the database set up
    prepare_db()

    # Everything prepared? Good. Here comes the main part.
    main()

    # close the database
    db_conn.close()

    # Do some important statistics
    logging.info("")
    logging.info("-------------------------------------------------------\n")
    logging.info("Start Time: " + str(start_time))
    end_time = datetime.datetime.now()
    logging.info("End Time: " + str(end_time))
    duration = end_time - start_time
    logging.info("Duration: " + str(duration) + "\n")
    logging.info("Processed Video Files: " + str(total_processed_videos))
    logging.info("Processed Picture Files: " + str(total_processed_pics))
    logging.info("Total Warnings:" + str(total_warnings))
