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

        time_zone_info = pytz.timezone('America/New_York')

        wrk_fire_counter = collection_counter.find({"fire_counter":True}).count()
        dataset = collection_counter.find({"fire_counter":True}).sort("incident_date")
        print('Incident# ', '{:<25}'.format('Date/Time'), '{:<30}'.format("Location"), '{:<30}'.format("Description"))
        for loop1 in dataset:
            wrk_incident_date = time_zone_info.localize(loop1["incident_date"])
            #print(loop1["incident_nbr"],  loop1["incident_date"], '{:<30}'.format(loop1["incident_location"][:30]), '{:<30}'.format(loop1["incident_description"][:30]))
            print(loop1["incident_nbr"], wrk_incident_date, '{:<30}'.format(loop1["incident_location"][:30]), '{:<30}'.format(loop1["incident_description"][:30]))

        print('Total Fire count:', wrk_fire_counter)


###---------------------------------------------------------------------
#  M a i n l i n e
###---------------------------------------------------------------------

wrk_class_email_counter = class_email_counter()
