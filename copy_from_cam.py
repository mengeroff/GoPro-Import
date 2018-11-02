import os
import time
import sys
import re
import datetime
import logging
import argparse
from shutil import copyfile
import sqlite3

import db_helper

class DbInfo(object):
    def __init__(self, db_cursor, db_conn):
        self._db_cursor = db_cursor
        self._db_conn = db_conn

    @property
    def db_cursor(self):
        return self._db_cursor

    @property
    def db_conn(self):
        return self._db_conn

    def close_connection(self):
        logging.info("Closing DB connection")
        self._db_conn.close()

    def execute(self, cmd):
        logging.debug("Executing DB command: " + cmd)
        self._db_cursor.execute(cmd)
        

class CamInfo(object):
    def __init__(self, cam_path, dest_path, db_path):
        self._cam_path = cam_path
        self._dest_path = dest_path
        self._db_path = db_path
        self._video_file_ext = [r'.*.mp4', r'.*.thm', r'.*.lrv']
        self._photo_file_ext = [r'.*.jpg', r'.*.gpr']
        self._total_processed_videos = 0
        self._total_processed_pics = 0
        self._total_warnings = 0
        
    @property
    def db_path(self):
        return self._db_path
    
    @property
    def video_file_ext(self):
        return self._video_file_ext

    @property
    def photo_file_ext(self):
        return self._photo_file_ext
    
    @property
    def total_processed_videos(self):
        return self._total_processed_videos

    def add_processed_video(self):
        self._total_processed_videos += 1

    @property
    def total_processed_pics(self):
        return self._total_processed_pics

    def add_processed_pic(self):
        self._total_processed_pics += 1

    @property
    def total_warnings(self):
        return self._total_warnings

    def add_warning(self):
        self._total_warnings += 1
       


def main(cam_info, db_info):
    """
    The main part of the script. It iterates though all files in the directory and the sub-directory,
    analyzes the files and copies them to the destination directory if required.

    :param cam_info class containing cam info
    :param db_info class containing db info
    :return: None
    """        
    # find those files to copy
    files_to_copy = analyze_files_to_copy(cam_info, db_info)

    # process each file
    process_files(cam_info, db_info, files_to_copy)


def analyze_files_to_copy(cam_info, db_info):
    """
    Check database and append only those files that need to be copied

    :param cam_info class containing cam info
    :param db_info class containing db info
    :return List of files that need to be copied
    """
    files_to_copy = []

    for root, __, files in os.walk(cam_info.cam_path, topdown=False):
        for file in files:
            path = os.path.join(root, file)
            logging.debug("file: " + path)

            date_created = extract_date(path)

            if db_helper.file_found(file, date_created, db_info.db_cursor):
                files_to_copy.append(file)

    return files_to_copy


def extract_date(path):
    date_created = datetime.datetime.strptime(time.ctime(os.path.getctime(path)), "%a %b %d %H:%M:%S %Y")
    date_created = date_created.strftime("%Y-%m-%d")
    return date_created


def process_files(cam_info, db_info, files_to_copy):
    """
    Process the list of files that need to be copied

    :param cam_info class containing cam info
    :param db_info class containing db info
    :param files_to_copy: The list containing all files that need to be processed
    """
    progress_iter = 0
    for root, __, files in os.walk(cam_info.cam_path, topdown=False):
        for name in files:
            if is_video_file(cam_info, name):
                process_general_file(cam_info, db_info, root, name)
                cam_info.add_processed_video()
            elif is_photo_file(cam_info, name):
                process_general_file(cam_info, db_info, root, name)
                cam_info.add_processed_pic()
            else:
                if not re.match(r'.*.sav', name.lower(), re.M | re.I):
                    logging.warning("unknown file format for file " + os.path.join(root, name))
                    cam_info.add_warning()

            progress_iter += 1
            print_progress(progress_iter, len(files_to_copy), prefix='Progress:')


def process_general_file(cam_info, db_info, root, name):
    """
    The processing step of the file, independent of the fact whether it's a photo or a video file.
    The creation date is determined and whether the file has already been copied to the destination.
    If so, it will not be copied again.

    :param cam_info class containing cam info
    :param db_info class containing db info
    :param root: The path to the file (without the actual file name)
    :param name: The file name with the extension
    :return: None
    """
    # determine destination path
    path = os.path.join(root, name)
    date_created = extract_date(path)
    directory = cam_info.dest_path + str()

    # check if file has already been copied
    db_info.execute("SELECT EXISTS(SELECT 1 FROM files WHERE file_name = ? AND date_created = ?)", (name, date_created,))
    data = db_info.db_cursor.fetchall()
    if data[0][0] == 0:
        # create folder with date
        if not os.path.exists(directory):
            os.makedirs(directory)

        # copy file
        dest = directory + "/" + name
        logging.info("Copying file from %s to %s" % (path, dest))
        copyfile(path, dest)

        # get file size
        file_size_bytes = os.path.getsize(path)
        file_size_mb = file_size_bytes / 1000000

        # add line to DB
        db_info.execute("INSERT INTO files VALUES ('%s','%s', '%s', %s)"
                        % (name, date_created, datetime.datetime.now().strftime("%Y-%m-%d"), file_size_mb))
        db_info.db_conn.db_conn.commit()
    else:
        logging.info("File %s already exists in destination %s. Skipping." % (path, directory))


def is_video_file(cam_info, name):
    """
    Check if the provided file is a video file.

    :param cam_info class containing cam info
    :param name: The name of the file with the extension
    :return: True, if it's a video file
    """
    for regex in cam_info.video_file_ext:
        match_obj = re.match(regex, name.lower(), re.M | re.I)
        if match_obj:
            return True

    return False


def is_photo_file(cam_info, name):
    """
    Check if the provided file is a photo file.

    :param cam_info class containing cam info
    :param name: The name of the file with the extension
    :return: True, if it's a photo file
    """
    for regex in cam_info.photo_file_ext:
        match_obj = re.match(regex, name.lower(), re.M | re.I)
        if match_obj:
            return True

    return False


def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=50):
    """
    Call in a loop to create terminal progress bar.

    :param iteration: Required  : current iteration (Int)
    :param total: Required  : total iterations (Int)
    :param prefix: Optional  : prefix string (Str)
    :param suffix: Optional  : suffix string (Str)
    :param decimals: Optional  : positive number of decimals in percent complete (Int)
    :param bar_length: Optional  : character length of bar (Int)
    :return: None
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)

    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),

    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()


def prepare_db(cam_info):
    """
    Preparation of the database. This means the creation of the cursor and of the table, if this table does
    not yet exist.

    :param cam_info class containing cam info
    :return: DbInfo class object
    """
    db_conn = sqlite3.connect(cam_info.db_path)
    db_cursor = db_conn.cursor()

    db_info = DbInfo(db_cursor, db_conn)

    # Create table
    db_info.execute("""
        CREATE TABLE IF NOT EXISTS files (file_name text, date_created text, date_copied text, size real)""")

    return db_info


def print_header():
    """
    Important printing of the project logo to the console and to the log output file.

    :return: None
    """
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
    """
    Preparation of the logging package.

    :return: None
    """
    numeric_level = getattr(logging, LOG_LEVEL.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % LOG_LEVEL)
    logging.basicConfig(
        filename=LOG_PATH + start_time.strftime("%Y-%m-%d-%H%M%S") + '_gopro_import.log',
        level=numeric_level,
        format='%(levelname)s:%(message)s'
    )
    getattr(logging, LOG_LEVEL.upper())


def parse_arguments():
    """
    Paring of the script arguments.

    :return: CamInfo class object
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("cam_path", required=True, help="The path to your GoPro.")
    parser.add_argument("dest_path", required=True, help="The path where you want to keep your GoPro files.")
    parser.add_argument("--log", required=False, 
                        help="Setting of the log level. Possible values are 'DEBUG', 'INFO', 'WARNING', 'ERROR', and 'CRITICAL'")
    args = parser.parse_args()

    LOG_PATH = args.dest_path + "logs/"
    db_path = LOG_PATH + "file_log.sqlite"
    cam_info = CamInfo(args.cam_path, args.dest_path, db_path)
    
    if args.log:
        LOG_LEVEL = args.log

    return cam_info


def log_statistics(cam_info):
    """
    Print statistics about the current job to the log file.

    :param cam_info class containing cam info
    :return: None
    """
    logging.info("")
    logging.info("-------------------------------------------------------\n")
    logging.info("Start Time: " + str(start_time))
    end_time = datetime.datetime.now()
    logging.info("End Time: " + str(end_time))
    duration = end_time - start_time
    logging.info("Duration: " + str(duration) + "\n")
    logging.info("Processed Video Files: " + str(cam_info.total_processed_videos))
    logging.info("Processed Picture Files: " + str(cam_info.total_processed_pics))
    logging.info("Total Warnings:" + str(cam_info.total_warnings))

    print("")
    print("-------------------------------------------------------\n")
    print("Start Time: " + str(start_time))
    print("End Time: " + str(end_time))
    print("Duration: " + str(duration) + "\n")
    print("Processed Video Files: " + str(cam_info.total_processed_videos))
    print("Processed Picture Files: " + str(cam_info.total_processed_pics))
    print("Total Warnings:" + str(cam_info.total_warnings))



if __name__ == '__main__':
    # first off get the current time as the starting time
    start_time = datetime.datetime.now()

    # initialize values for logging
    LOG_PATH = ""
    LOG_LEVEL = "INFO"

    # parse the arguments
    cam_info = parse_arguments()

    # prepare the logging environment
    prepare_logging()

    # print the header to the log file and the console. We want to see what we're dealing with.
    print_header()

    # get the database set up
    db_info = prepare_db(cam_info)

    # Everything prepared? Good. Here comes the main part.
    main(cam_info, db_info)

    # close the database
    db_info.close_connection()

    # Do some important statistics
    log_statistics(cam_info)
