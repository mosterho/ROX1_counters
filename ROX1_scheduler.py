###
##
## Schedule the ROX1Update program to run every ## minutes
## It's probably better to use something like systemctl,
## but just trying this

import sys, subprocess, time

wrk_time = int(sys.argv[1])

while 1==1:
    print("\r{:60s}\r".format('Update running...'), end='', flush=True)
    subprocess.run(['python3', 'ROX1_update_ROX1db.py'])
    for i in range(wrk_time, 0, -60):
        #print('\rJob sleeping... seconds remaining: ' + "{:4d}".format(i) + '\r', end='', flush=True)
        print("\r{:60s}\r".format('Job sleeping... time remaining: ' + "{:2d}".format(int(i/60)) + " minutes"), end='', flush=True)
        time.sleep(60)
