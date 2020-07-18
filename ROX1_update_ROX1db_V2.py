###
## open the "dispatches" mailbox, accumulate, print and update
## the fire and EMS incident numbers in a Mongo collection
##
## See the following link on using imap and email
## https://www.thepythoncode.com/article/reading-emails-in-python
##


import sys, email, ROX1_logging, ROX1_IMAP_access, pytz, argparse
import logging
#from datetime import datetime, date, time, tzinfo
from datetime import datetime, date
from operator import itemgetter
from pymongo import MongoClient

class cls_container:
    def __init__(self, arg_mailbox_class, arg_rebuild, arg_verbose):
        self.mailbox_class = arg_mailbox_class
        self.rebuild = arg_rebuild
        self.verbose = arg_verbose
        self.overall_firecount = 0
        self.overall_firecount_co1 = 0
        self.overall_emscount = 0
        self.overall_emscount_co1 = 0
        self.overall_duplicatecount = 0
        self.overall_emailcount = 0
        self.overall_emailcount2 = 0
        self.overall_emailcount3 = 0
        self.incident_list = []
        self.apparatus_list = []
        self.local_timezone = pytz.timezone('America/New_York')
        self.UTC_timezone =   pytz.timezone('UTC')

        #logging.basicConfig(filename='logging/ROX1_CAD.log',level=logging.DEBUG)
        #logging.info(self.fct_datetime_now() + ' *'*30)
        #logging.info(self.fct_datetime_now() + ' __init__ started...')
        ROX1_logging.fct_ROX1_log('info', sys.argv[0], ' *'*30)
        ROX1_logging.fct_ROX1_log('info', sys.argv[0], str(' __init__' +  ' started...'))

        ## connect to Mongo collection
        client = MongoClient('mongodb')
        db = client.ROX1db
        self.collection_CADdata = db.CADdata
        self.collection_CADapparatus = db.CADapparatus
        self.collection_apparatus = db.TBLapparatus

        ## check argument to clear data from CAD collection
        if(self.rebuild == 'Y'):
            self.collection_CADdata.delete_many({})
            self.collection_CADapparatus.delete_many({})
            if(self.verbose >= 1):
                print('CAD data deleted')
            #logging.info(self.fct_datetime_now() + ' CAD data deleted...')
            ROX1_logging.fct_ROX1_log('info', sys.argv[0], ' CAD data deleted...')

    def fct_datetime_now(self):
        wrk_currentdt = datetime.now()
        wrk_dtstring = wrk_currentdt.strftime('%Y %b %d %H:%M:%S')
        return wrk_dtstring + ' ' + sys.argv[0]

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
                                    ROX1_logging.fct_ROX1_log('error', sys.argv[0], str('*** ERROR get_payload failed on 2nd attempt: ' + str(e)))
                                        #logging.error(fct_datetime_now() + ' ********** ERROR: Get_payload failed on 2nd attempt using straight string' + e)
                                    break
                            self.fct_email_parse(body)
                            self.overall_emailcount3 += 1  # add to counter, even if parse encountered duplicate email

    def fct_search_string(self, arg_base_text):
        ## return email search date (e.g., 01-JAN-2020) and additional text
        wrk_date_today = date.today()
        wrk_build_string = ''
        #wrk_build_string = 'SINCE 01-JAN-' + str(wrk_date_today.year)
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
        tmp_incident_flag, tmp_flag_apparatus_header, tmp_flag_apparatus_header2, tmp_flag_apparatus_header3 = False, False, False, False
        this_incident_nbr = ''
        inc_date = ''
        inc_time = ''
        inc_description = ''
        inc_location = ''
        inc_fire = False
        inc_fire_co1 = False
        inc_ems = False
        inc_ems_co1 = False
        inc_apparatus = ''

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
            if('Start Dt     Time       Situation/Description' in x and not tmp_startdate_flag):  ## Set flag to read next line, this contains the desired date_tuple
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
            if("Location                                                        C/A  USE   OPER" in x and tmp_flag_location1 in(0,1)):
                tmp_flag_location1 += 1
            elif("Location                                                        C/A  USE   OPER" not in x and
                tmp_flag_location1 >= 1 and inc_location == ''):
                inc_location = x

            ## Check next section of email for apparatus details
            if("Unit       Dispatch  Enroute  Arrived   Okay   Area Chk   Avail   Cleared" in x and tmp_flag_apparatus_header == False):
                tmp_flag_apparatus_header = True
            elif(x[20:22].isnumeric() and tmp_flag_apparatus_header):  # x[20:22] is "enroute" time
                rtn_co1, rtn_companynbr, rtn_fireems = self.fct_validate_apparatus(x[:6])
                if(rtn_fireems == 'ems'):
                    inc_ems = True
                    if(rtn_co1 == True):
                        inc_ems_co1 = True
                elif(rtn_fireems == 'fire'):
                    inc_fire = True
                    if(rtn_co1 == True):
                        inc_fire_co1 = True
                if(rtn_fireems != ''):
                    self.fct_apparatus_update(x, this_incident_nbr, 'section1')

            if("Unit        EnSta    ArSta    EnHosp   ArHosp  Hospital  EnJail   ArJail" in x and tmp_flag_apparatus_header2 == False):
                tmp_flag_apparatus_header, tmp_flag_apparatus_header2 = False, True
            elif(x[11:13].isnumeric() and tmp_flag_apparatus_header2 == True):  # x[11:13] is EnSta time
                self.fct_apparatus_update(x, this_incident_nbr, 'section2')
            if("Unit       Reduce Speed Reason         Recalled Reason          Staged" in x and tmp_flag_apparatus_header3 == False):
                tmp_flag_apparatus_header2, tmp_flag_apparatus_header3 = False, True
            elif(tmp_flag_apparatus_header3):
                #self.fct_apparatus_update(x, this_incident_nbr, 'section3')
                pass  #for future
            if('E911 Information:' in x[:17]):
                break
        ## Append the incident list, this will be used to update the Mongo database
        self.incident_list.append([this_incident_nbr, inc_date, inc_time,
            inc_description[:43].rstrip(), inc_location[:63].rstrip(), inc_fire, inc_fire_co1, inc_ems, inc_ems_co1])

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
            #logging.info(self.fct_datetime_now() + ' ******* DUPLICATE INCIDENT: ' + tmp_incident_nbr)
            ROX1_logging.fct_ROX1_log('info', sys.argv[0], str('DUPLICATE INCIDENT: ' +  tmp_incident_nbr))
            self.overall_duplicatecount += 1
        cursor = self.collection_CADdata.find({"incident_nbr":tmp_incident_nbr})
        try:
            for readit in cursor:
                rtn_flag = ''
                #break
        except:
            pass
        return rtn_flag

    def fct_apparatus_update(self, arg_x, arg_incident_number, arg_section):
        try:
            wrk_x = arg_x
            wrk_incident_number = arg_incident_number
            wrk_section = arg_section
            wrk_x_split = wrk_x.split()
            # section1 is for the first header encountered for apparatus times
            if(arg_section == 'section1'):
                if(wrk_x[11:13] != '  '):
                    wrk_dispatch = str(wrk_x[11:19])
                else:
                    wrk_dispatch = ''
                if(wrk_x[20:28] != '        '):
                    wrk_enroute = str(wrk_x[20:28])
                else:
                    wrk_enroute = ''
                if(wrk_x[29:37] != '        '):
                    wrk_arrive = str(wrk_x[29:37])
                else:
                    wrk_arrive = ''
                if(wrk_x[56:64] != '        '):
                    wrk_available = str(wrk_x[56:64])
                else:
                    wrk_available = ''
                if(wrk_x[65:73] != '        '):
                    wrk_cleared = wrk_x[65:73]
                else:
                    wrk_cleared = ''
                self.apparatus_list.append([wrk_incident_number + '_' + wrk_x_split[0],
                    wrk_dispatch, wrk_enroute, wrk_arrive, wrk_available, wrk_cleared])
                #pass
            elif(arg_section == 'section2'):
                if(wrk_x[11:13] != '  '):
                    wrk_enroutestation = str(wrk_x[11:19])
                else:
                    wrk_enroutestation = ''
                if(wrk_x[29:37] != '        '):
                    wrk_enroutehosp = str(wrk_x[29:37])
                else:
                    wrk_enroutehosp = ''
                if(wrk_x[38:46] != '        '):
                    wrk_arrivehosp = str(wrk_x[38:46])
                else:
                    wrk_arrivehosp = ''
                tmp_count = 0
                for i in self.apparatus_list:
                    if(i[0] == wrk_incident_number + '_' + wrk_x_split[0]):
                        self.apparatus_list[tmp_count].extend([wrk_enroutestation, wrk_enroutehosp, wrk_arrivehosp])
                        #logging.info(self.fct_datetime_now() + ' ** TEMP info apparatus found in list in fct_apparatus_update: ')
                    tmp_count += 1
                #pass
            elif(arg_section == 'section3'):
                pass
            #logging.info(self.fct_datetime_now() + ' info apparatus list in fct_apparatus_update: ' + str(self.apparatus_list))
        except Exception as E:
            #logging.info(self.fct_datetime_now() + ' info/warning during fct_apparatus_update: ' + E)
            ROX1_logging.fct_ROX1_log('info', sys.argv[0], str('warning encountered during apparatus update: ' +  str(E)))

    def fct_update_collection(self):
        ### update the incident details
        for x in self.incident_list:
            UTC_datetime = ''
            if(x[1] != ''):
                ## Force datetime to UTC
                try:
                    wrk_datetime_tmp = datetime.strptime(x[1] + " " + x[2], "%x %X")
                    converted_datetime_local = self.local_timezone.localize(wrk_datetime_tmp)
                    UTC_datetime = converted_datetime_local.astimezone(self.UTC_timezone)
                    #print(converted_datetime_local, ' ', UTC_datetime)
                except Exception as E:
                    if(self.verbose >= 1):
                        print('Error during timezone conversion: ', E)
                    #logging.error(self.fct_datetime_now() + ' Error during timezone conversion: ' + E)
                    ROX1_logging.fct_ROX1_log('error', sys.argv[0], str('Errror during timezone conversion: ' + str(E)))
                #print('***** just before insert', wrk_datetime, '  ', self.local_timezone.localize(wrk_datetime))
            self.collection_CADdata.insert_one({"incident_nbr": x[0], "incident_date":UTC_datetime,
                "incident_description":x[3], "incident_location":x[4], "fire_counter":x[5], "fire_counter_co1":x[6], "ems_counter":x[7] , "ems_counter_co1":x[8]})

        ### Now update the CAD apparatus details
        for x in self.apparatus_list:
            #pass
            try:
                if(len(x)>6):
                    tmp_enroutestation = x[6]
                    tmp_enroutehospital = x[7]
                    tmp_arrivehospital = x[8]
                else:
                    tmp_enroutestation = ''
                    tmp_enroutehospital = ''
                    tmp_arrivehospital = ''
                self.collection_CADapparatus.insert_one({"incident_nbr": x[0][0:10], "apparatus":x[0][11:17], "dispatch":x[1],
                    "enroute":x[2], "arrive_scene":x[3],
                    "enroute_hospital":tmp_enroutehospital, "arrive_hospital":tmp_arrivehospital,
                    "enroute_station":tmp_enroutestation, "available":x[4], "clear":x[5]})
            except Exception as E:
                #logging.error(self.fct_datetime_now() + ' Error while assigning values to apparatus CADdata collection: ' + E + '\n' + x)
                ROX1_logging.fct_ROX1_log('error', sys.argv[0], str('Error while assigning values to apparatus CADapparatus collection: ' + str(E) + '\n' + x))

    def fct_validate_apparatus(self, arg_apparatus):
        try:
            cursor = self.collection_apparatus.find({"apparatus":arg_apparatus})
            wrk_co1, wrk_companynbr, wrk_fireems = False, 0, ''
            for x in cursor:
                #wrk_co1 = x[co1]
                wrk_companynbr = x['company']
                if(wrk_companynbr == 1):
                    wrk_co1 = True
                if(arg_apparatus[:1] == 'E'):
                    wrk_fireems = 'ems'
                elif(arg_apparatus[:1]) == 'F':
                    wrk_fireems = 'fire'
        except Exception as e:
            ROX1_logging.fct_ROX1_log('error', sys.argv[0], str('Error while validating apparatus: ' + str(e) + ' ' + str(x)))
        return wrk_co1, wrk_companynbr, wrk_fireems

    def fct_sortandprint(self):
        print_ctr = 0
        tmp_incident_list = sorted(self.incident_list, key=itemgetter(1,2))  #sort by date and time
        print("Print incident list")
        for inc_data in tmp_incident_list:
            print(inc_data[0], ' ', inc_data[1], ' ', inc_data[2], ' ', inc_data[3], ' ', inc_data[4], ' ' )
            ROX1_logging.fct_ROX1_log('info', sys.argv[0], str(' ADDED to CAD collection: ' + inc_data[0] +
                ' ' + inc_data[1] + ' ' + inc_data[2] + ' ' + inc_data[3] + ' ' + inc_data[4]))
        print("End of Print incident list")

    def fct_finish(self, arg_mailbox_class):
        try:
            arg_mailbox_class.fct_cleanup()
        except:
            if(self.verbose >= 1):
                print('Issue logging out of mailbox')
            #logging.error(self.fct_datetime_now() + ' Issue logging out of mailbox' )
            ROX1_logging.fct_ROX1_log('error', sys.argv[0], str('Issue logging out of mailbox'))
        if(self.verbose >= 2):
            print('Overall  (F) fire counter:', self.overall_firecount)
            print('Overall   (E) ems counter:', self.overall_emscount)
            print('Overall duplicate counter:', self.overall_duplicatecount)
            print('Overall           counter:', self.overall_firecount + self.overall_emscount + self.overall_duplicatecount)
            print('Overall     email counter:', self.overall_emailcount)
            print('Overall    email2 counter:', self.overall_emailcount2)
            print('Overall    email3 counter:', self.overall_emailcount3)
        if(self.verbose >= 1):
            print('  Incidents added counter:', len(self.incident_list))
        #logging.info(self.fct_datetime_now() + ' Incidents added counter: ' + str(len(self.incident_list)))
        ROX1_logging.fct_ROX1_log('info', sys.argv[0], str('Incidents added counter: ' + str(len(self.incident_list))))

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

    # Read and process all emails in the INBOXs (depending on the rebuild option), then
    # read list just created and load into MongoDB collection
    if(rslt_parser.rebuild == 'Y'):
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.1-2017')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.2-2017')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.3-2017')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.4-2017')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.5-2017')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.6-2017')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.7-2017')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.8-2017')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.9-2017')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.10-2017')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.11-2017')
        wrk_container.fct_read_email(wrk_class, 'INBOX.Archived.12-2017')

        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.1-2018')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.2-2018')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.3-2018')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.4-2018')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.5-2018')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.6-2018')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.7-2018')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.8-2018')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.9-2018')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.10-2018')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.11-2018')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2018.12-2018')

        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.1-2019')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.2-2019')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.3-2019')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.4-2019')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.5-2019')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.6-2019')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.7-2019')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.8-2019')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.9-2019')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.10-2019')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.11-2019')
        wrk_container.fct_read_email(wrk_class, 'INBOX.2019.12-2019')

    wrk_container.fct_read_email(wrk_class, 'INBOX')
    wrk_container.fct_update_collection()

    # Sort and print the detailed results from reading the inbox
    if(rslt_parser.verbose >= 1):
        wrk_container.fct_sortandprint()

    # print summary, perform cleanup on mail server
    wrk_container.fct_finish(wrk_class)
