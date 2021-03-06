// Stages that have been excluded from the aggregation pipeline query
__3tsoftwarelabs_disabled_aggregation_stages = [

	{
		// Stage 4 - excluded
		stage: 4,  source: {
			$match: {
			    "monthofcall":05
			}
		}
	},

	{
		// Stage 6 - excluded
		stage: 6,  source: {
			$match: {
			    "dayofweek":{$in: [1,7]}
			}
		}
	},

	{
		// Stage 7 - excluded
		stage: 7,  source: {
			$match: {
			    "hourofcall":{$in:[9,10,11,12,13,14,15,16,17,18,19,20,21,22]}
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
