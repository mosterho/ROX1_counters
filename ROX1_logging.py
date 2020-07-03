###
# logging module for ROX1 programs

import sys, logging, datetime

def fct_ROX1_log(arg_loglevel, arg_program, arg_text):
    logging.basicConfig(filename='logging/ROX1_CAD.log',level=logging.DEBUG)
    wrk_currentdt = datetime.datetime.now()
    wrk_dtstring = wrk_currentdt.strftime('%Y %b %d %H:%M:%S')
    wrk_beginning_string = wrk_dtstring + ' ' + arg_program
    if(arg_loglevel == 'error'):
        logging.error(wrk_beginning_string + ' *** ERROR: ' + arg_text)
    elif(arg_loglevel == 'info'):
        logging.info(wrk_beginning_string + ' INFO: ' + arg_text)

if(__name__ == '__main__'):
    fct_ROX1_log(sys.argv[1], sys.argv[2], sys.argv[3])
