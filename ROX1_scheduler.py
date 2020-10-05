###
##
## Schedule the ROX1Update program to run every ## minutes
## It's probably better to use something like systemctl,
## but just trying this

import sys, subprocess, time, ROX1_logging, argparse
#from termcolor import colored

wrk_parser = argparse.ArgumentParser(usage="The ROX1 Scheduler program will call the ROX1 Update program via continuous loop with a sleep time of ### seconds based on the argument. Arguments include 1. time (in seconds) to sleep and then rerun the Update (integer)")
wrk_parser.add_argument("time", help="Run the Update program every ### seconds (default = 1800).", type=int, default=1800)
rslt_parser = wrk_parser.parse_args()

wrk_time = rslt_parser.time  # time to sleep in seconds

try:
    while 1==1:
        # notes: the \r{:60s}\r along with the end='' keeps the print statements on the same line
        # (\r is carriage return without new line, 60s is 60 long string, end='' changes the default \n to empty string)
        # the '\033[91m' produces red color, the '\033[0m' at the end of the string resets the color
        print("\r{:60s}\r".format('\033[91mUpdate running...do not hit Ctrl+C...\033[0m'), end='', flush=True)
        subprocess.run(['python3', 'ROX1_update_ROX1db_V2.py'])
        for i in range(wrk_time, 0, -60):
            print("\r{:60s}\r".format('Job sleeping... job restart in ' + "{:2d}".format(int(i/60)) + " minutes"), end='', flush=True)
            time.sleep(60)
except Exception as e:
    ROX1_logging.fct_ROX1_log('error', sys.argv[0], str(e))
    print('Error encountered in ' + sys.argv[0] + ' ' + str(e))
