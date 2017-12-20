# Since Gdax limit the number of datapoints it returns
# We will be making multiple requests going back X days in the past 
# Then append all into the same csv file in order

from datetime import datetime, timedelta
from dateutil import parser
import time
import pandas as pd
import xchange_reader as xr

cur_day  = "2017-12-19"
cur_date = cur_day + "T23:00:00.000000Z"
ndays = 2 # number of days to go behind
granularity = 600 # 10 minutes
currency = 'LTC-EUR'

xreader = xr.XChangeReader()

# loop through the start date and end date and append to the Dataframe

end   = parser.parse(cur_date)
start = end - timedelta(days=1)

total_frame = pd.DataFrame() # create an empty dataframe

for i in range(0, ndays):
    
    retry_flag = True
    iso_start  = "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(start) 
    iso_end    = "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(end)
        
    print("Start: " + iso_start)
    print("End: " + iso_end + "\n")
    
    while retry_flag:
        try:
            df = xreader.read_gdaxdata(start, end, granularity, currency, False,False)
            retry_flag = False
            total_frame = total_frame.append(df)
        except ValueError:
            print("Failed to Read, Retrying...")
            retry_flag = True
            time.sleep(2)
     
   
    print(total_frame)
    end   = start
    start = start - timedelta(days=1)
    time.sleep(5)

# save the total frame into a csv file
total_frame = total_frame.iloc[::-1]  # reverse for ascending time
total_frame.to_csv( currency + "-" + str(granularity) + '-history.csv')
    
    
    