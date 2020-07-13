// Stages that have been excluded from the aggregation pipeline query
__3tsoftwarelabs_disabled_aggregation_stages = [

	{
		// Stage 3 - excluded
		stage: 3,  source: {
			$match: {
			    "yearofcall":2020
			}
		}
	},

	{
		// Stage 4 - excluded
		stage: 4,  source: {
			$match: {
			    "incident_nbr": /^E.*/i
			}
		}
	},

	{
		// Stage 6 - excluded
		stage: 6,  source: {
			$bucket: {
			    groupBy: "$ems_counter", // usually "$path.to.field"
			    boundaries: [ false, true ],
			    default: "true", // optional
			    output: { count: { $sum: 1 } } // optional
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

		// Stage 2
		{
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
		},

		// Stage 5
		{
			$sort: {
			    "incident_date" : 1
			}
		},
	],

	// Options
	{
		allowDiskUse: true
	}

	// Created with Studio 3T, the IDE for MongoDB - https://studio3t.com/

);
