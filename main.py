from src.apg_gui import run as run_gui
from src.apg import run
import sys


def main():
    args = sys.argv
    
    if len(args) == 1:
        run_gui(path_config='./config.ini', path_style='./styles/style.qss')
    elif args[1] == "0":
        run(path_config='./config.ini')

if __name__=="__main__":
    main()