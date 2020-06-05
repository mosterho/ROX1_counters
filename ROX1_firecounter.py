###
## Fire counter for white board

import sys, pytz
from pymongo import MongoClient
#from datetime import datetime, date, time, tzinfo

class class_email_counter:
    def __init__(self):

        client = MongoClient('Ubuntu18Server01')
        db = client.ROX1db
        collection_counter = db.CADdata

        my_timezone = pytz.timezone('America/New_York')
        UTC_timezone = pytz.timezone('UTC')

        wrk_email_counter, wrk_fire_counter = 0, 0
        dataset = collection_counter.find({"$or":[{"incident_nbr":{"$regex":"^F"}}, {"fire_counter":True}]}).sort("incident_date")
        print('Email', 'Incident# ', '{:<25}'.format('Date/Time'), '{:<30}'.format("Location"), '{:<30}'.format("Description"))
        for loop1 in dataset:
            wrk_incident_tmp = UTC_timezone.localize(loop1["incident_date"])
            wrk_incident_date = wrk_incident_tmp.astimezone(my_timezone)
            if(loop1["fire_counter"]):
                wrk_email_only = ''
            else:
                wrk_email_only = 'X'
            print('{:^5}'.format(wrk_email_only), loop1["incident_nbr"], wrk_incident_date, '{:<30}'.format(loop1["incident_location"][:30]), '{:<30}'.format(loop1["incident_description"][:30]))
            wrk_email_counter += 1
            if(loop1["fire_counter"]):
                wrk_fire_counter += 1

        print('Total email count:', wrk_email_counter)
        print(' Total fire count:', wrk_fire_counter)


###---------------------------------------------------------------------
#  M a i n l i n e
###---------------------------------------------------------------------

wrk_class_email_counter = class_email_counter()
