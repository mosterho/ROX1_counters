###
## open the "dispatches" mailbox, accumulate, print and count
## the fire and EMS incident numbers and their respective totals
##

import sys, ROX1_IMAP_access
from datetime import datetime, date, time
from operator import itemgetter
from pymongo import MongoClient

class cls_container():
    def __init__(self, arg_mailbox_class):
        self.mailbox_class = arg_mailbox_class
        self.overall_firecount = 0
        self.overall_emscount = 0
        self.incident_list = []

    def fct_read_email(self, arg_mailbox_class, arg_mailboxfolder):
        arg_mailbox_class.CADEmails.select(mailbox=arg_mailboxfolder, readonly=True)
        wrk_search_date = self.fct_date_string()
        wrk_search_string = '(BODY "3691") SINCE ' + wrk_search_date
        #typ, data = arg_mailbox_class.CADEmails.search(None, '(BODY "3691") (SINCE 1-JAN-2020)')
        typ, data = arg_mailbox_class.CADEmails.search(None, wrk_search_string)
        for num in data[0].split():
            typ2, data2 = arg_mailbox_class.CADEmails.fetch(num, "(BODY.PEEK[TEXT])")
            ## For whatever reason, sometimes there is b')' in data2[0][1]
            ## Use TRY: to avoid errors with  .decode
            try:
                decoded_bodytext = data2[0][1].decode()
                split_bodytext = decoded_bodytext.splitlines()
            except:
                split_bodytext = ''
            ## go through individual lines of email body, find incident number, etc.
            tmp_startdate_flag, tmp_startdate_flag2 = False, False
            for x in split_bodytext:
                x_split = x.split()
                if(x[:13] == 'Event Number:'):  #F201140011
                    this_incident_nbr = x[14:24]
                    tmp_return = self.fct_event_number(this_incident_nbr)
                elif(x[:45] == 'Start Dt     Time       Situation/Description'):  ## Set flag to read next line, this contains the desired date_tuple
                    tmp_startdate_flag = True
                elif(tmp_startdate_flag and x[2:3] == '/' and x[5:6] == '/'): # 04/24/20 16:23:37  FND: 252   SMELL/ODOR/SOUND OF GAS LEAK INSIDE BUILD
                    #tmp_startdate_flag2 = True
                    inc_date = x_split[0]
                    inc_time = x_split[1]
                    tmp_special = x.split(maxsplit=4)  # special split to get full incident description
                    inc_description = tmp_special[4]
                    self.incident_list.append((this_incident_nbr, inc_date, inc_time, inc_description[:44].rstrip()))
                    break
        arg_mailbox_class.CADEmails.close()

    def fct_date_string(self):
        ## Subtract days and return email search date (e.g., 16-MAY-2020)
        wrk_date_delta = date.today()
        wrk_build_string = '01-JAN-' + str(wrk_date_delta.year)
        #print(wrk_date_delta, '  ', wrk_build_string)
        return wrk_build_string

    def fct_event_number(self, arg_incident_nbr):
        tmp_incident_nbr = arg_incident_nbr
        rtn_flag = ''
        if(tmp_incident_nbr not in self.incident_list):
            if(tmp_incident_nbr[:1] == 'F'):
                self.overall_firecount += 1
                rtn_flag = 'F'
            if(tmp_incident_nbr[:1] == 'E'):
                self.overall_emscount += 1
                rtn_flag = 'E'
        return rtn_flag

    def fct_update_collection(self):
        client = MongoClient('Ubuntu18Server01')
        db = client.ROX1fd
        collection_counter = db.FD_Counter
        collection_counter.delete_many({})

        for x in self.incident_list:
            cursor = collection_counter.find({"incident_nbr": x[0]})
            if(cursor):
                for cursor_data in cursor:
                    if(cursor_data):
                        pass
            #else:
            wrk_datetime = datetime.strptime(x[1] + " " + x[2], "%m/%d/%y %H:%M:%S")
            collection_counter.insert_one({"incident_nbr": x[0], "incident_date":wrk_datetime, "incident_description":x[3]})

    def fct_sortandprint(self):
        print_ctr = 0
        tmp_incident_list = sorted(self.incident_list, key=itemgetter(1,2))  #sort by date and time
        for inc_data in tmp_incident_list:
            print(inc_data)

    def fct_finish(self, arg_mailbox_class):
        #arg_mailbox_class.CADEmails.logout()
        try:
            arg_mailbox_class.fct_cleanup()
        except:
            print('Issue logging out of mailbox')
        print('Overall fire_counter:', self.overall_firecount)
        print('Overall  ems_counter:', self.overall_emscount)

#############################################################
### Begin mainline

if (__name__ == "__main__"):

    ## create a class object that connected to the mail server only
    wrk_class = ROX1_IMAP_access.cls_CAD_emails()

    ## create a second class that contains the mail server class from above
    ## This will contain the functions, etc. to read the emails from the mail server class
    wrk_container = cls_container(wrk_class)

    # Read a nd process the emails in the INBOX
    wrk_container.fct_read_email(wrk_class, 'INBOX')

    # Read list just created and load into MongoDB collection
    wrk_container.fct_update_collection()

    # Sort and print the detailed results from reading the inbox
    wrk_container.fct_sortandprint()

    # print summary, perform cleanup on mail server
    wrk_container.fct_finish(wrk_class)
