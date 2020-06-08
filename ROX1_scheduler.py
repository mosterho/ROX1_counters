###
##
## Schedule the ROX1Update program to run every ## minutes
## It's probably better to use something like systemctl,
## but just trying this

import sys, subprocess, time

while 1==1:
    print('\rUpdate running...                        \r', end='', flush=True)
    subprocess.run(['python3', 'ROX1_update_ROX1db.py'])
    for i in range(int(sys.argv[1]), 0, -60):
        #print('\rJob sleeping... seconds remaining: ' + "{:4d}".format(i) + '\r', end='', flush=True)
        print('\rJob sleeping... time remaining: ' + "{:2d}".format(int(i/60)) + " minutes ", end='', flush=True)
        time.sleep(60)
