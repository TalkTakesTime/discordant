import logging
from sys import stdout
from datetime import datetime
import os


def get_default_logfile():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    elif not os.path.isdir(log_dir):
        raise IOError('cannot write to default log directory (./{})'.format(
                log_dir))
    return '{}/{}.log'.format(log_dir, datetime.now()).replace(':', '.')


def configure_logging(logfile=None, logfile_level=logging.DEBUG,
                      stdout_level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(logfile_level)
    format_str = '%(asctime)s (%(levelname)s) - %(name)s: %(message)s'

    # log all messages to a log file
    if logfile is None:
        logfile = get_default_logfile()
    file_handler = logging.FileHandler(filename=logfile, encoding='utf-8',
                                       mode='w')
    file_handler.setLevel(logfile_level)
    file_handler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(file_handler)

    # log info or higher messages to stdout
    stdout_handler = logging.StreamHandler(stdout)
    stdout_handler.setLevel(stdout_level)
    stdout_handler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(stdout_handler)
