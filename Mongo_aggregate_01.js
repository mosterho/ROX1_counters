db.getCollection("CADdata").aggregate(

	// Pipeline
	[
		// Stage 1
		{
			$addFields: {
			    "incident_year": {$year:"$incident_date"}
			}
		},

		// Stage 2
		{
			$bucket: {
			    groupBy: "$incident_year", // usually "$path.to.field"
			    boundaries: [ 2017,2018,2019,2020,9999 ],
			    default: "Unknown", // optional
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
