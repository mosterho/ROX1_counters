db.getCollection("CAD_data").aggregate(

	// Pipeline
	[
		// Stage 1
		{
			$addFields: {
			     proj_incdate: {
			          $dateToParts: { date: "$incident_date", timezone: "America/New_York" }
			       }
			}
		},

		// Stage 2
		{
			$match: {
			"ems_counter" : false, "incident_nbr":{"$regex": "^E"},  "incident_dayofweek" : { 
			            "$elemMatch" : { 
			                "$in" : [
			                    5.0, 
			                    6.0
			                ]
			            }
			        }
			}
		},
	],

	// Options
	{
		allowDiskUse: true
	}

	// Created with Studio 3T, the IDE for MongoDB - https://studio3t.com/

);
