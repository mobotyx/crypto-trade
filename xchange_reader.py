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


    # overload of the previous one but this one takes into consideration the 
    # previous day and append the previous volume to the current day into the dataframe
    def read1_gdaxdata(self, start, end, p_start, p_end, granularity, currency):
        # request the gdax API
        d = self.__gdax_public.get_product_historic_rates(currency, granularity=granularity, start=start, end=end)
        time.sleep(2)
        d_prev = self.__gdax_public.get_product_historic_rates(currency, granularity=granularity, start=p_start, end=p_end)

        # setup two data-frames for current and previous day
        # and save them into csvs
        ds = [d_prev, d]
        dfc = []

        is_curr = False
        dd = None
        for dc in ds:
            df = pd.DataFrame(dc)
            df.columns = ['timestamp', 'low', 'high', 'open', 'close', 'volume']
            df.insert(1, 'datetime', '')
            df['datetime'] = df['timestamp'].apply(datetime.fromtimestamp)
            df = df.set_index('timestamp')

            df['high-low'] = df['high'] - df['low']
            df['close-low'] = df['close'] - df['low']
            df['high-close'] = df['high'] - df['close']
            df['close-open'] = df['close'] - df['open']
            df['(high-close/hi-low)%'] = (1.0 - df['high-close'] / abs(df['high-low'])) * 100

            df['RG'] = ""

            for index, row in df.iterrows():
                if float(row['close-open']) > 0:
                    df.loc[index, 'RG'] = 'GREEN'
                else:
                    df.loc[index, 'RG'] = 'RED'

            if is_curr:
                df.insert(6, 'volume-prev', 0.0)
                for index0, row0 in dfc[0].iterrows():
                    for index1, row1 in df.iterrows():
                        if row0['datetime'].time() == row1['datetime'].time():
                            df.loc[index1, 'volume-prev'] = float(row0['volume'])

            is_curr = True

            df = df.iloc[::-1] # reverse for ascending time
            dfc.append(df)
            df.to_csv('csv/prices/' + currency + "/" + currency + " " + datetime.fromtimestamp(dc[0][0]).strftime("%B %d, %Y ") + str(granularity) + '.csv')
    
        return dfc
