###
## open the "dispatches" mailbox, accumulate, print and update
## the fire and EMS incident numbers in a Mongo collection
##
## See the following link on using imap and email
## https://www.thepythoncode.com/article/reading-emails-in-python
##


import sys, email, ROX1_IMAP_access, pytz, argparse
from datetime import datetime, date, time, tzinfo
from operator import itemgetter
from pymongo import MongoClient

class cls_container:
    def __init__(self, arg_mailbox_class, arg_rebuild, arg_verbose):
        self.mailbox_class = arg_mailbox_class
        self.rebuild = arg_rebuild
        self.verbose = arg_verbose
        self.overall_firecount = 0
        self.overall_emscount = 0
        self.overall_duplicatecount = 0
        self.overall_emailcount = 0
        self.overall_emailcount2 = 0
        self.overall_emailcount3 = 0
        self.incident_list = []
        self.time_zone_info = pytz.timezone('America/New_York')
        self.UTC_timezone =   pytz.timezone('UTC')
        self.dct_dayofweek = {
        0: "Monday", 1:"Tuesday", 2:"Wednesday", 3:"Thursday", 4:"Friday", 5:"Saturday", 6:"Sunday"
        }

        client = MongoClient('Ubuntu18Server01')
        db = client.ROX1db
        self.collection_counter = db.CADdata

        if(self.rebuild == 'Y'):
            self.collection_counter.delete_many({})
            if(self.verbose >= 1):
                print('CAD collection deleted')

    def fct_read_email(self, arg_mailbox_class, arg_mailboxfolder):
        wrk_nbr_emails_ = arg_mailbox_class.CADEmails.select(mailbox=arg_mailboxfolder, readonly=True)
        wrk_parserclass = email.parser.BytesParser()
        ## See function "fct_search_string" for additional built-in text with date
        wrk_search_string = self.fct_search_string('FROM Dispatch')
        typ, data = arg_mailbox_class.CADEmails.search(None, wrk_search_string)
        #### num contains the email ID to retrieve
        for num in data[0].split():
            typ2, data2 = arg_mailbox_class.CADEmails.fetch(num, "RFC822")  # retrieve list of email numbers
            self.overall_emailcount += 1
            for data2_i in data2:
                ## Checking for tuple will skip the b')' entry at the end of each email
                if(isinstance(data2_i, tuple)):
                    wrk_message = wrk_parserclass.parsebytes(data2_i[1])
                    # work our way thru the email to the "text/html:" content
                    for part in wrk_message.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/html":
                            self.overall_emailcount2 += 1
                            try:
                                body = part.get_payload(decode=True).decode()
                            except Exception as e:
                                #print('********** ERROR: Get_payload failed on 1st attempt using "decode"', e)
                                try:
                                    body = part.get_payload()
                                except Exception as e:
                                    if(self.verbose >= 1):
                                        print('********** ERROR: Get_payload failed on 2nd attempt using straight string', e)
                                    break
                            self.fct_email_parse(body)
                            self.overall_emailcount3 += 1  # add to counter, even if parse encountered duplicate email

    def fct_search_string(self, arg_base_text):
        ## return email search date (e.g., 01-JAN-2020) and additional text
        wrk_date_today = date.today()
        wrk_build_string = 'SINCE 01-JAN-' + str(wrk_date_today.year)
        #wrk_build_string += ' OR (BODY "3691") (OR BODY "36109" BODY "36110")'
        wrk_build_string += ' ' + arg_base_text
        return wrk_build_string

    def fct_email_parse(self, arg_email):
        try:
            split_bodytext = arg_email.splitlines()
        except:
            split_bodytext = ''
        ## go through individual lines of email body, find incident number, etc.
        tmp_startdate_flag, tmp_startdate_found_flag, tmp_startdate_flag2, tmp_flag_location1, tmp_flag_location2 = False, False, False, 0, False
        tmp_incident_flag, tmp_flag_apparatus_header = False, False
        this_incident_nbr = ''
        inc_date = ''
        inc_time = ''
        inc_description = ''
        inc_location = ''
        inc_fire = False
        inc_ems = False
        apparatus_list = []

        for x in split_bodytext:
            x_split = x.split()
            #print(x)
            if(x[:13] == 'Event Number:' and tmp_incident_flag == False):  #F201140011
                this_incident_nbr = x[14:24]
                tmp_return = self.fct_event_number(this_incident_nbr)
                # tmp_return will normally have an 'F' or 'E'
                # if tmp_return is blank/empty string, this was a duplicate email
                if(tmp_return == ''):
                    return
                tmp_incident_flag = True
                #print('debugging inc#:', this_incident_nbr)
            if(x[:45] == 'Start Dt     Time       Situation/Description'):  ## Set flag to read next line, this contains the desired date_tuple
                tmp_startdate_flag = True
            elif(tmp_startdate_flag and x[2:3] == '/' and x[5:6] == '/' and not tmp_startdate_found_flag): # 04/24/20 16:23:37  FND: 252   SMELL/ODOR/SOUND OF GAS LEAK INSIDE BUILD
                inc_date = x_split[0]
                inc_time = x_split[1]
                #print(type(inc_date), inc_date, '   ', type(inc_time), inc_time)
                tmp_special = x.split(maxsplit=4)  # special split to get full incident description
                try:
                    if(tmp_special[4][30:40] != ''):
                        inc_description = tmp_special[4]
                except:
                    inc_description = "*** Unexpected data/format of description"
                tmp_startdate_found_flag = True
            #elif(inc_description == '' and inc_date != ''):   # once in a while, the description is on the line after date/time (e.g., E201170031)
                #inc_description = x.split[2]
            if(x[:] == "Location                                                        C/A  USE   OPER" and tmp_flag_location1 in(0,1)):
                tmp_flag_location1 += 1
            elif(x[:] != "Location                                                        C/A  USE   OPER" and tmp_flag_location1 >= 1 and inc_location == ''):
                inc_location = x
            if(x[:] == "Unit       Dispatch  Enroute  Arrived   Okay   Area Chk   Avail   Cleared" and tmp_flag_apparatus_header == False):
                tmp_flag_apparatus_header = True
            elif((x[:6] in('E36109', 'E36110')) and x[20:22].isnumeric() and inc_ems == False):  # x[20:22] is "enroute" time
                inc_ems = True
            elif((x[:4] == '3691' or x[:6] in ("F36BC1","F36Q11","F36E12","F36E13","F36T14","F36R16")) and inc_fire == False):
                inc_fire = True
                #print(this_incident_nbr, '  ', x)

        ## Append the incident list, this will be used to update the Mongo database
        self.incident_list.append([this_incident_nbr, inc_date, inc_time, inc_description[:43].rstrip(), inc_location[:63].rstrip(), inc_fire, inc_ems])

    def fct_event_number(self, arg_incident_nbr):
        tmp_incident_nbr = arg_incident_nbr
        rtn_flag = ''
        tmp_list = [x[0] for x in self.incident_list]  ## Create a temporary list of existing incident numbers to lookup
        if(tmp_incident_nbr not in tmp_list):
            if(tmp_incident_nbr[:1] == 'F'):
                self.overall_firecount += 1
                rtn_flag = 'F'
            if(tmp_incident_nbr[:1] == 'E'):
                self.overall_emscount += 1
                rtn_flag = 'E'
        else:
            if(self.verbose >= 1):
                print('******* DUPLICATE INCIDENT: ', tmp_incident_nbr)
            self.overall_duplicatecount += 1
        cursor = self.collection_counter.find({"incident_nbr":tmp_incident_nbr})
        try:
            for readit in cursor:
                rtn_flag = ''
                #break
        except:
            pass
        return rtn_flag

    def fct_update_collection(self):

        for x in self.incident_list:
            UTC_datetime = ''
            if(x[1] != ''):
                ## Force datetime to UTC
                try:
                    wrk_datetime_tmp = datetime.strptime(x[1] + " " + x[2], "%x %X")
                    #print('*** ', type(x[1]), '  ', type(x[2]), '  ', type(wrk_datetime_tmp))
                    converted_datetime_local = self.time_zone_info.localize(wrk_datetime_tmp)
                    UTC_datetime = converted_datetime_local.astimezone(self.UTC_timezone)
                    #print(converted_datetime_local, ' ', UTC_datetime)
                except Exception as E:
                    if(self.verbose >= 1):
                        print('Error during timezone conversion: ', E)
                #print('***** just before insert', wrk_datetime, '  ', self.time_zone_info.localize(wrk_datetime))
            self.collection_counter.insert_one({"incident_nbr": x[0], "incident_date":UTC_datetime, "incident_description":x[3], "incident_location":x[4], "fire_counter":x[5], "ems_counter":x[6]})

    def fct_sortandprint(self):
        print_ctr = 0
        tmp_incident_list = sorted(self.incident_list, key=itemgetter(1,2))  #sort by date and time
        print("Print incident list")
        for inc_data in tmp_incident_list:
            print(inc_data[0], ' ', inc_data[1], ' ', inc_data[2], ' ', inc_data[3], ' ', inc_data[4], ' ' )
        print("End of Print incident list")

    def fct_finish(self, arg_mailbox_class):
        #
        try:
            arg_mailbox_class.fct_cleanup()
        except:
            if(self.verbose >= 1):
                print('Issue logging out of mailbox')
        if(self.verbose >= 1):
            print('Overall  (F) fire_counter:', self.overall_firecount)
            print('Overall   (E) ems_counter:', self.overall_emscount)
            print('Overall duplicate counter:', self.overall_duplicatecount)
            print('Overall           counter:', self.overall_firecount + self.overall_emscount + self.overall_duplicatecount)
            print('Overall     email counter:', self.overall_emailcount)
            print('Overall    email2 counter:', self.overall_emailcount2)
            print('Overall    email3 counter:', self.overall_emailcount3)
            print('  Incidents added counter:', len(self.incident_list))

#############################################################
### Begin mainline

if (__name__ == "__main__"):

    ## work with argument parser to build correct parameter/argument values
    wrk_parser = argparse.ArgumentParser(usage="The ROX1 Update program will update the CAD data from emails received in the Dispatches email. Arguments include 1. Rebuild the CAD collection (Y,N)  2. printing/debugging info")
    wrk_parser.add_argument("-r", "--rebuild", help="Rebuild the CAD collection (i.e., delete all data and start from scratch). 'Y' will rebuild the CAD collection, 'N' (default) will add new entries only.", choices=['Y', 'N'], default='N')
    wrk_parser.add_argument("-v", "--verbose", help="Specifiy the level of vebose output, valid values are -v and -vv", action="count", default=0)
    rslt_parser = wrk_parser.parse_args()

    ## create a class object that connected to the mail server only
    wrk_class = ROX1_IMAP_access.cls_CAD_emails()

    ## create a second class that contains the mail server class from above
    ## This will contain the functions, etc. to read the emails from the mail server class
    wrk_container = cls_container(wrk_class, rslt_parser.rebuild, rslt_parser.verbose)

    # Read a nd process the emails in the INBOX
    wrk_container.fct_read_email(wrk_class, 'INBOX')

    # Read list just created and load into MongoDB collection
    wrk_container.fct_update_collection()

    # Sort and print the detailed results from reading the inbox
    if(rslt_parser.verbose >= 2):
        wrk_container.fct_sortandprint()

    # print summary, perform cleanup on mail server
    wrk_container.fct_finish(wrk_class)
