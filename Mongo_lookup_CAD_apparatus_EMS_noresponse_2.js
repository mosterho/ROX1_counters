// Stages that have been excluded from the aggregation pipeline query
__3tsoftwarelabs_disabled_aggregation_stages = [

	{
		// Stage 2 - excluded
		stage: 2,  source: {
			$lookup: // Equality Match
			{
			    from: "CADapparatus",
			    localField: "incident_nbr",
			    foreignField: "incident_nbr",
			    as: "wrk_apparatus_fields"
			}
			
			// Uncorrelated Subqueries
			// (supported as of MongoDB 3.6)
			// {
			//    from: "<collection to join>",
			//    let: { <var_1>: <expression>, …, <var_n>: <expression> },
			//    pipeline: [ <pipeline to execute on the collection to join> ],
			//    as: "<output array field>"
			// }
		}
	},

	{
		// Stage 4 - excluded
		stage: 4,  source: {
			$match: {
			    "monthofcall":05
			}
		}
	},

	{
		// Stage 10 - excluded
		stage: 10,  source: {
			$bucketAuto: {
			    groupBy: "$ems_counter", // usually "$path.to.field"
			    buckets: 4, // number of buckets
			    output: { count: { $sum: 1 } }, // optional
			    //granularity: "" // optional, supported: "R5", "R10", "R20", "R40", "R80", "1-2-5", "E6", "E12", "E24", "E48", "E96", "E192", "POWERSOF2" 
			}
		}
	},
]

db.getCollection("CADdata").aggregate(

	// Pipeline
	[
		// Stage 1
		{
			$addFields: {
			    "dayofweek": {$dayOfWeek: "$incident_date" }, 
			    "hourofcall":{$hour: "$incident_date"}, 
			    "yearofcall":{$year:"$incident_date"}, "monthofcall":{$month:"$incident_date"},
			    //"hourofcall2":{$hour: {"$incident_date", timezone:"America/New_York"}}
			}
		},

		// Stage 3
		{
			$match: {
			    "yearofcall":2020
			}
		},

		// Stage 5
		{
			$match: {
			    "incident_nbr": /^E.*/i
			}
		},

		// Stage 6
		{
			$match: {
			    "dayofweek":{$in: [1,7]}
			}
		},

		// Stage 7
		{
			$match: {
			    "hourofcall":{$in:[9,10,11,12,13,14,15,16,17,18,19,20,21,22]}
			}
		},

		// Stage 8
		{
			$sort: {
			    "incident_date" : 1
			}
		},

		// Stage 9
		{
			$bucket: {
			    groupBy: "$ems_counter", // usually "$path.to.field"
			    boundaries: [ false, true ],
			    default: "true", // optional
			    output: { count: { $sum: 1 } } // optional
			}
		},
	],

	// Options
	{
		allowDiskUse: true
	}

	// Created with Studio 3T, the IDE for MongoDB - https://studio3t.com/

);
