Flight ticket search tool

The python script allows to find flight tickets in a given data table, between given origin and destination, including indirect flights as well if layover time 1-6 hours.

operation:

- check required and optional parameters (if a required parameter is missing -> error message & exiting)
- collect all the connections between origin and destination (a left join is used)
- calculate time difference
- omit those connections, which can not meet the layover time constraint
- calculate summarizing columns (eg. total_time, total_price)
- transform data frame similar to json format (concatenating columns, formatting)
- order table by total_price
- extract result in json format


parameters:
- input_file : str
    File name of the input file (csv, must be in the same directory where .py is).
- orig : str 
    Origin Airport. (must be one of the origin airports listed in the input file)
- dest : str
    Destionation Airport. (must be one of the destination airports listed in the input file)
- bags : int,  default = 0
    optional parameter, number of bags 
- return : boolean, default=False
    optional parameter, is it a return flight?


how to run?

python -m kiwi_final.py example3.csv NNB VVH --bags=2 
