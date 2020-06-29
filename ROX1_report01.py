###
## Fire counter for white board

import sys, pytz, datetime, argparse
from pymongo import MongoClient
from datetime import date


class class_email_counter:
    def __init__(self, arg_organization, arg_year):

        client = MongoClient('mongodb')
        db = client.ROX1db
        collection_counter = db.CADdata

        my_timezone = pytz.timezone('America/New_York')
        UTC_timezone = pytz.timezone('UTC')

        if(arg_year == 0):
            wrk_year = date.year()
        else:
            wrk_year = arg_year

        wrk_email_counter, wrk_fire_counter = 0, 0
        wrk_finddate = datetime.datetime(wrk_year,1,1,0,0,0)
        wrk_finddate2 = datetime.datetime(wrk_year,12,31,0,0,0)
        if(arg_organization == 'fire'):
            dataset = collection_counter.find({ "$or": [ { "fire_counter": True }, { "incident_nbr": {"$regex": "F.*" }} ],
                "incident_date": {"$gte": wrk_finddate, "$lte": wrk_finddate2} }).sort("incident_date")
        elif(arg_organization == 'ems'):
            dataset = collection_counter.find({ "$or": [ { "ems_counter": True }, { "incident_nbr": {"$regex": "E.*" }} ],
                "incident_date": {"$gte": wrk_finddate, "$lte": wrk_finddate2} }).sort("incident_date")

        print('Email', 'Incident# ', '{:<25}'.format('Date/Time'), '{:<30}'.format("Location"), '{:<30}'.format("Description"))
        for loop1 in dataset:
            wrk_incident_tmp = UTC_timezone.localize(loop1["incident_date"])
            wrk_incident_date = wrk_incident_tmp.astimezone(my_timezone)
            if(loop1["fire_counter"] or loop1['ems_counter']):
                wrk_email_only = ''
            else:
                wrk_email_only = 'X'
            print('{:^5}'.format(wrk_email_only), loop1["incident_nbr"], wrk_incident_date, '{:<30}'.format(loop1["incident_location"][:30]), '{:<30}'.format(loop1["incident_description"][:30]))
            wrk_email_counter += 1
            if(wrk_email_only == ''):
                wrk_fire_counter += 1

        print('Total email count:', wrk_email_counter)
        print(' Total count:', wrk_fire_counter)

    class cls_grab_current_year():
        def __init__(self):
            return date.year()


###---------------------------------------------------------------------
#  M a i n l i n e
###---------------------------------------------------------------------

wrk_parser = argparse.ArgumentParser(usage="The Counter program provides a report of the CAD data from the Mongo database collection ''CADData''. Arguments include 1. ems or fire (ems, fire)  2. year (4 digit int)")
wrk_parser.add_argument("organization", help="Select the agency to include. 'ems' and 'fire' are the available choices", choices=['ems', 'fire'])
wrk_parser.add_argument("year", help="Enter the four digit year for the calls to include", type=int, default=0)
rslt_parser = wrk_parser.parse_args()

wrk_class_email_counter = class_email_counter(rslt_parser.organization, rslt_parser.year)
