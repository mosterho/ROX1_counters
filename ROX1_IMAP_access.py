###
## open the "dispatches" mailbox,
##

import sys, logging
import imaplib, ssl, hashlib, json
from cryptography.fernet import Fernet
from datetime import datetime, date

class cls_CAD_emails():
    def __init__(self):
        logging.basicConfig(filename='logging/ROX1_CAD.log',level=logging.DEBUG)
        try:
            ### open file and retrieve email info
            self.wrk_login, self.wrk_hash, self.wrk_pwd, self.wrk_salt = '', '', '', ''
            ## read the json file to get values
            self.fct_read_json()
            ### initial test for SSL to server comes back with error for TLS
            mailbox_context = ssl.create_default_context()
            self.CADEmails = imaplib.IMAP4_SSL(host=self.wrk_host, port=993)
            #self.CADEmails.starttls(ssl_context=mailbox_context)   # error message that TLS is not supported (??)
            # running NETSTAT in another window while running this program shows port 993 is open

            self.CADEmails.login(self.wrk_login, self.wrk_pwd)
            self.overall_firecount = 0
            self.overall_emscount = 0
            self.incident_list = []
            # create empty passlib object
        except Exception as e:
            logging.error(fct_datetime_now() + ' ********** ERROR: cls_CAD_emails in ' + ' failed as follows: ' + e)

    def fct_read_json(self):
        try:
            wrk_jsonfile = open('../Additional/data.json')
            wrk_json = json.load(wrk_jsonfile)
            wrk_jsonfile.close()
            self.wrk_publickey = wrk_json["publickey"]
            self.wrk_salt = wrk_json["salt"]
            self.wrk_host = wrk_json["host"]
            self.wrk_login = wrk_json["login"]
            ###
            ### decrypt using cryptography/Fernet
            # encode text to bytes
            tmp_key = self.wrk_publickey.encode()
            # create cypher object
            cipher_suite = Fernet(tmp_key)
            #
            tmp_pwd = wrk_json["pwd"]
            tmp_password = tmp_pwd.encode()
            # decrypt password and set the class work variable
            tmp_decrypted_password = cipher_suite.decrypt(tmp_password)
            self.wrk_pwd = tmp_decrypted_password.decode()
            #print("pwd:", (self.wrk_pwd))
        except Exception as e:
            logging.error(fct_datetime_now() + ' ********** ERROR: fct_read_json in ' + ' failed as follows: ' + e)

    def fct_datetime_now(self):
        wrk_currentdt = datetime.now()
        wrk_dtstring = wrk_currentdt.strftime('%Y %b %d %H:%M:%S')
        return wrk_dtstring + ' ' + sys.argv[0]

    def fct_cleanup(self):
        try:
            self.CADEmails.close()
            self.CADEmails.logout()
        except Exception as e:
            logging.error(fct_datetime_now() + ' ********** ERROR: fct_cleanup ' + ' failed as follows: ' + e)

#############################################################
### Begin mainline

if (__name__ == "__main__"):

    wrk_class = cls_CAD_emails()
    wrk_class.fct_cleanup()
