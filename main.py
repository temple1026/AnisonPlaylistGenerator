import datetime
import logging
import os
import sys
from logging import getLogger

from src.apg import run
from src.apg_gui import run as run_gui


def main():
    args = sys.argv
    
    dir_log = "./logs"
    if not os.path.isdir(dir_log):
        os.makedirs(dir_log)

    fmt = "%(lineno)d: %(asctime)s: %(levelname)s: %(name)s: %(module)s: %(message)s"
    path_log = os.path.join(dir_log, str(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")) + ".log")
    logging.basicConfig(filename=path_log, level=logging.INFO, format=fmt)
    logger = getLogger(__name__)
        

    if len(args) == 1:
        run_gui(path_config='./config.ini', path_style='./styles/style.qss', logger=logger)
    elif args[1] == "0":
        run(path_config='./config.ini')

if __name__=="__main__":
    main()
