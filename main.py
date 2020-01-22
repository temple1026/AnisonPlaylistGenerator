from apg_gui import run as run_gui
from apg import run
import sys


def main():
    args = sys.argv
    
    if len(args) == 1:
        run_gui()
    elif args[1] == "0":
        run()

if __name__=="__main__":
    main()