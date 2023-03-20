import logging
import time
import json

from utils import check_dir


class TerminalColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def pprint(o):
    if type(o) == str:
        try:
            return json.dumps(json.loads(o), indent=4, sort_keys=True)
        except ValueError:
            return o
    elif type(o) == dict or type(o) == list:
        return json.dumps(o, indent=4, sort_keys=True)
    return str(o)


def console(s):
    print(TerminalColors.OKBLUE + "[" + get_time() + "] " + pprint(s) + TerminalColors.ENDC)


def print_warning(s):
    print(TerminalColors.WARNING + "[" + get_time() + "] WARN " + pprint(s) + TerminalColors.ENDC)


def log(s):
    print(TerminalColors.FAIL + "[" + get_time() + "] ERROR " + pprint(s) + TerminalColors.ENDC)


def get_logger(log_dir, name):
    log_dir = check_dir(log_dir)
    logger = logging.getLogger(name)
    file_path = log_dir / "{}.log".format(name)
    hdlr = logging.FileHandler(file_path)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    return logger
