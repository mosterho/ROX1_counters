// Stages that have been excluded from the aggregation pipeline query
__3tsoftwarelabs_disabled_aggregation_stages = [

	{
		// Stage 5 - excluded
		stage: 5,  source: {
			$match: {
			    "yearofcall":2020
			}
		}
	},

	{
		// Stage 8 - excluded
		stage: 8,  source: {
			$bucket: {
			    groupBy: "$concat_ems", // usually "$path.to.field"
			    boundaries: [ "b", "z" ],
			    default: "", // optional
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
			    "yearofcall":{$year:"$incident_date"}, 
			    "monthofcall":{$month:"$incident_date"},
			    "ems_counter_string":{$convert:{input:"$ems_counter", to:"string"}},
			    "ems_counter_co1_string":{$convert:{input:"$ems_counter_co1", to:"string"}}
			    //"yearofcall_str":{$convert:{input:"$yearofcall", to:"string"}}
			    //"concat_ems":{$concat:["$ems_counter_string", "$ems_counter_co1_string"]}
			    //"hourofcall2":{$hour: {"$incident_date", timezone:"America/New_York"}}
			}
		},

		// Stage 2
		{
			$addFields: {
			    "yearofcall_str":{$convert:{input:"$yearofcall", to:"string"}},
			    //"concat_ems":{$concat:["$yearofcall_str", "$ems_counter_string", "$ems_counter_co1_string"]},
			    //"concat_ems":{$concat:["$ems_counter_string", "$ems_counter_co1_string"]}
			}
		},

		// Stage 3
		{
			$addFields: {
			    "concat_ems":{$concat:["$yearofcall_str", "$ems_counter_string", "$ems_counter_co1_string"]}
			}
		},

		// Stage 4
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

		// Stage 6
		{
			$match: {
			    "incident_nbr": /^E.*/i
			}
		},

		// Stage 7
		{
			$sort: {
			    "incident_date" : 1
			}
		},

		// Stage 9
		{
			$bucketAuto: {
			    groupBy:"$concat_ems", // usually "$path.to.field"
			    buckets: 15, // number of buckets
			    output: { count: { $sum: 1 } }, // optional
			    //granularity: "" // optional, supported: "R5", "R10", "R20", "R40", "R80", "1-2-5", "E6", "E12", "E24", "E48", "E96", "E192", "POWERSOF2" 
			}
		},
	],

	// Options
	{
		allowDiskUse: true
	}

	// Created with Studio 3T, the IDE for MongoDB - https://studio3t.com/

);
