###
##
## Schedule the ROX1Update program to run every ## minutes
## It's probably better to use something like systemctl,
## but just trying this

import sys, subprocess, time, ROX1_logging

wrk_time = int(sys.argv[1])  # time to sleep in seconds

try:
    while 1==1:
        print("\r{:60s}\r".format('Update running...'), end='', flush=True)
        subprocess.run(['python3', 'ROX1_update_ROX1db.py'])
        for i in range(wrk_time, 0, -60):
            print("\r{:60s}\r".format('Job sleeping... job restart in ' + "{:2d}".format(int(i/60)) + " minutes"), end='', flush=True)
            time.sleep(60)
except Exception as e:
    ROX1_logging.fct_ROX1_log('error', sys.argv[0], str(e))
    print('Error encountered in ' + sys.argv[0] + ' ' + str(e))
