import gdax
from datetime import datetime, timedelta
import time
import pandas as pd
from dateutil import parser


class XChangeReader: 
    
    def __init__(self):
        self.__gdax_public =  gdax.PublicClient() 
    
    # Server time is in UTC. 
    def get_gdaxtime(self):
        stime = self.__gdax_public.get_time()['epoch']
        return datetime.fromtimestamp(int(stime))


    # Reads Prices from GDAX exchange API between a start datetime and an end datetime 
    # granularity in seconds for distance between each datapoint 
    # currency indicate the currency to which we request ex. 'LTC-EUR'
    # save_csv indicate if we want to keep a copy into a csv file of the data
	# ex. read_gdaxdata("2017-12-18T23:00:00.000000Z", "2017-12-19T23:00:00.000000Z", 600, 'LTC-EUR', False,False)
	# ex. return between midnight 19/12 and 23h50 19/12 
    def read_gdaxdata(self, start, end, granularity, currency, save_csv = False, reverse=False):
    
        d = self.__gdax_public.get_product_historic_rates(currency, granularity=granularity, start=start, end=end)
        # build the dataframe 
        df = pd.DataFrame(d)
        df.columns = ['timestamp', 'low', 'high', 'open', 'close', 'volume']
        df.insert(1, 'datetime', '')
        df['datetime'] = df['timestamp'].apply(datetime.fromtimestamp)
        df = df.set_index('timestamp')

        # Add some insight data
        df['close-open'] = df['close'] - df['open']
        df['RG'] = ""

        for index, row in df.iterrows():
            if float(row['close-open']) > 0:
                df.loc[index, 'RG'] = 'GREEN'
            else:
                df.loc[index, 'RG'] = 'RED'

        if reverse:
            df = df.iloc[::-1] # reverse for ascending time

        if save_csv:
            df.to_csv('csv/prices/' + currency + "/" + currency + " " + datetime.fromtimestamp(d[0][0]).strftime("%B %d, %Y ") + str(granularity) + '.csv')
    
        return df
    
    # Read the same way as in polling the API but get the data from a csv file instead
    # This helps accelerate back-testing without having to poll the API
    # Stat and End are assumed to be given in UTC
    def read_gdaxcsvdata(self, start, end, file_path):
        df = None
        # try opening the file given 
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            print('read_gdaxcsvdata: File Not Found Error')
            return None
        except Exception:
            print('Unexpeced error Occured')
            return None

        # convert to timestamp
        start_ts = int(parser.parse(start).timestamp())
        end_ts   = int(parser.parse(end).timestamp())

        return df.loc[(df.timestamp >= start_ts) & (df.timestamp < end_ts)]

        # get a sub dataframe between start and end date
    
    # retun the first timestamp (oldest) in the csv file if found
    def get_gdaxcsv_timestamp(self, file_path, select='first'):
        df = None
        # try opening the file given 
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            print('read_gdaxcsvdata: File Not Found Error')
            return None
        except Exception:
            print('Unexpeced error Occured')
            return None

        if select == 'first':
            return int(df.iloc[0]['timestamp'])
        elif select == 'last':
            return int(df.iloc[len(df.index)-1]['timestamp'])
        else:
            return None

    # get granulariy in te given file 
    def get_gdaxcsv_granularity(self, file_path):
        df = None
        # try opening the file given 
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            print('read_gdaxcsvdata: File Not Found Error')
            return None
        except Exception:
            print('Unexpeced error Occured')
            return None

        return int(df.iloc[1]['timestamp']) - int(df.iloc[0]['timestamp'])
