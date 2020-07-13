### Roxbury (NJ) Fire and EMS Company #1

This folder contains programs that analyze fire and EMS calls for the township. The data are stored in a MongoDB
database. There are a mix of Python programs and MongoDB aggregate scripts in this folder.

 Two of the programs take advantage of the "argument parser" module. This assists with calling the program using flags for argument passing, including -h for help.

There are currently five Python programs used in this system:
* ROX1_update_ROX1db.py: This is the main program used for reading CAD emails and updating the MongoDB collections. This uses the argument parser module.
* ROX1_IMAP_access.py: This program provides the connection to the CAD mailbox.
* ROX1scheduler.py: This program runs in a continuous loop; the way to start it is open a command prompt and run it. To stop it hit  CTRL-C. This program accepts an argument with time (in seconds) to run the ROX1update_ROX1db.py program.
* ROX1_logging.py: This program takes advantage of the "logging" module. The program accepts three arguments and writes to the "ROX1_CAD.log" log file. Sample entries in the log file appears as follows:
  - INFO:root:2020 Jul 11 15:26:03 ROX1_update_ROX1db.py INFO:  __init__ started...
  - INFO:root:2020 Jul 11 15:26:03 ROX1_update_ROX1db.py INFO:  CAD data deleted...
  - INFO:root:2020 Jul 11 15:26:09 ROX1_update_ROX1db.py INFO: DUPLICATE INCIDENT: E170770033

  The arguments for the program are:
  - Log level: valid values are "info" and "error"
  - Program/module name: embedded as text alongside date/time
  - Text: any information that will be included in the log entry
* ROX1_report01.py: This program provides a report of CAD entries. This uses the argument parser module. There are two arguments:
  - organization: Valid values are "fire" or "ems" (both lowercase)
  - year: the four digit year

There are also a handful of .js files used in the MongoDB client "Studio 3T". These .js files are used for MongoDB aggregation query jobs.
