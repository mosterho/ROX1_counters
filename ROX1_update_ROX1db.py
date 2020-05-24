###
## open the "dispatches" mailbox, accumulate, print and count
## the fire and EMS incident numbers and their respective totals
##
## See the following link on using imap and email
## https://www.thepythoncode.com/article/reading-emails-in-python
##


import sys, email, ROX1_IMAP_access
from datetime import datetime, date, time
from pymongo import MongoClient

class cls_container():
    def __init__(self, arg_mailbox_class):
        self.mailbox_class = arg_mailbox_class
        self.overall_firecount = 0
        self.overall_emscount = 0
        self.overall_emailcount = 0
        self.overall_emailcount2 = 0
        self.overall_emailcount3 = 0
        self.incident_list = []
        self.helpcounter = 0  ## Very temporary for debugging

    def fct_read_email(self, arg_mailbox_class, arg_mailboxfolder):
        wrk_nbr_emails_ = arg_mailbox_class.CADEmails.select(mailbox=arg_mailboxfolder, readonly=True)
        wrk_parserclass = email.parser.BytesParser()
        ## Build the search string based on station, apparatus (EMS)

        #wrk_search_string = self.fct_search_string('BODY "3691"')
        wrk_search_string = self.fct_search_string('FROM Dispatch')
        typ, data = arg_mailbox_class.CADEmails.search(None, wrk_search_string)

        #### KEEP THE FOLLOWING 2 LINES (for now)!!
        #wrk_search_string = self.fct_search_string('OR BODY "36109" BODY "36110" NOT BODY "3691"')
        #typ, data = arg_mailbox_class.CADEmails.search(None, 'SINCE 1-JAN-2020')

        typ, data = arg_mailbox_class.CADEmails.search(None, wrk_search_string)
        for num in data[0].split():
            typ2, data2 = arg_mailbox_class.CADEmails.fetch(num, "RFC822")
            self.overall_emailcount += 1
            #print(typ2, ' ', data2)
            for data2_i in data2:
                ## Checking for tuple will skip the b')' entry
                if(isinstance(data2_i, tuple)):
                    wrk_message = wrk_parserclass.parsebytes(data2_i[1])
                    for part in wrk_message.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/html":
                            self.overall_emailcount2 += 1
                            try:
                                # get the email body
                                body = part.get_payload(decode=True).decode()
                            except:
                                #print('********** Get_payload didn"t work for ', wrk_message)
                                pass
                            try:
                                #print(body)
                                self.fct_email_parse(body)
                                self.overall_emailcount3 += 1
                            except:
                                pass
                                #print('********** my code for email parse didn"t work for ', wrk_message)

        arg_mailbox_class.CADEmails.close()

    def fct_email_parse(self, arg_email):
        try:
            #decoded_bodytext = data2[0][1].decode()
            #decoded_bodytext = arg_email
            split_bodytext = arg_email.splitlines()
        except:
            split_bodytext = ''
        ## go through individual lines of email body, find incident number, etc.
        tmp_startdate_flag, tmp_startdate_flag2, tmp_flag_location1, tmp_flag_location2 = False, False, 0, False
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
                tmp_incident_flag = True
                #if(tmp_return == ''):
                    #break
            if(x[:45] == 'Start Dt     Time       Situation/Description'):  ## Set flag to read next line, this contains the desired date_tuple
                tmp_startdate_flag = True
            elif(tmp_startdate_flag and x[2:3] == '/' and x[5:6] == '/'): # 04/24/20 16:23:37  FND: 252   SMELL/ODOR/SOUND OF GAS LEAK INSIDE BUILD
                #tmp_startdate_flag2 = True
                inc_date = x_split[0]
                inc_time = x_split[1]
                tmp_special = x.split(maxsplit=4)  # special split to get full incident description
                try:
                    if(tmp_special[4][30:40] != ''):
                        inc_description = tmp_special[4]
                    #else:
                        #inc_description = "*** Unexpected data/format of description"
                except:
                    inc_description = "*** Unexpected data/format of description"
            #elif(inc_description == '' and inc_date != ''):   # once in a while, the description is on the line after date/time (e.g., E201170031)
                #inc_description = x.split[2]
            if(x[:] == "Location                                                        C/A  USE   OPER" and tmp_flag_location1 in(0,1)):
                tmp_flag_location1 += 1
            elif(x[:] != "Location                                                        C/A  USE   OPER" and tmp_flag_location1 >= 1 and inc_location == ''):
                inc_location = x
            if(x[:] == "Unit       Dispatch  Enroute  Arrived   Okay   Area Chk   Avail   Cleared" and tmp_flag_apparatus_header == False):
                tmp_flag_apparatus_header = True
            elif((x[:6] == 'E36109' or x[:6] == 'E36110') and x[20:22].isnumeric()  and x[29:31].isnumeric and inc_ems == False):  # x[29:37] is "arrived" time
                inc_ems = True
                print(this_incident_nbr, '  ', x)
                break

        ## Append the incident list, this will be used to update the Mongo database
        self.helpcounter += 1
        if(this_incident_nbr[0] == 'E' and '3691' in arg_email or this_incident_nbr[0] == 'F'):
            inc_fire = True
        #if(this_incident_nbr[0] == 'F' and ('E36109' in arg_email or 'E36110' in arg_email)):
            #inc_ems = True
        self.incident_list.append((this_incident_nbr, inc_date, inc_time, inc_description[:43].rstrip(), inc_location[:63].rstrip(), inc_fire, inc_ems))

    def fct_search_string(self, arg_base_text):
        ## return email search date (e.g., 16-MAY-2020)
        wrk_date_delta = date.today()
        wrk_build_string = 'SENTSINCE 01-JAN-' + str(wrk_date_delta.year)
        #wrk_build_string += ' OR (BODY "3691") (OR BODY "36109" BODY "36110")'
        wrk_build_string += ' ' + arg_base_text
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
        db = client.ROX1db
        collection_counter = db.CAD_data
        collection_counter.delete_many({})

        for x in self.incident_list:
            print(x)
            #else:
            try:
                wrk_datetime = datetime.strptime(x[1] + " " + x[2], "%m/%d/%y %H:%M:%S")
            except:
                pass
            collection_counter.insert_one({"incident_nbr": x[0], "incident_date":wrk_datetime, "incident_description":x[3], "incident_location":x[4], "fire_counter":x[5], "EMS_counter":x[6]})

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
        print('Overall  fire_counter:', self.overall_firecount)
        print('Overall   ems_counter:', self.overall_emscount)
        print('Overall       counter:', self.overall_firecount + self.overall_emscount)
        print('Overall email counter:', self.overall_emailcount)
        print('Overall email2 counter:', self.overall_emailcount2)
        print('Overall email3 counter:', self.overall_emailcount3)
        print('          PGM counter:', len(self.incident_list))

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
    #wrk_container.fct_sortandprint()

    # print summary, perform cleanup on mail server
    wrk_container.fct_finish(wrk_class)
