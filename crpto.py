#!/usr/bin/python
import sys, getopt
from datetime import datetime, timedelta
import time
import pandas as pd
from dateutil import parser
import ntplib
import os 

import xchange_reader as xr
import strategy as stg
import money_pool as mp
import technical_indicators as ti

file = None 
ntp_server = 'europe.pool.ntp.org'
investment = 1000                       # Initial Allocated budget
currency = 'LTC-EUR'                    # currency
granularity = 600                       # We gather points spaced 10 minutes each
backtest_file_path = "./market-data/LTC-EUR-600-history.csv" # Note: this file must contain price points with the same spacing as granularity
memory = 4                              # 6 times granularity - This is the time-horizon we look into the past
### BEST RUN for MA crossover algorithm is a memory of 4 x 10 minutes.
### TODO: check to fill gaps in data an rerun

def LogPrint(str_line):
    print(str_line)
    file.write(str_line + '\n')

# Real Time Run - Getting information directly from the Exchange
# First read the Data from the exchange between NOW and granularity*memory in the past
# Run the stategy to get BUY or SELL signals 
# we sleep everytime the amount of granularity
def run_realtime(xreader, strategy):
    ntp = ntplib.NTPClient() # to get UTC time
    while(True):
        # Get UTC time since this is the actual server time used
        # Go back some seconds back to get a proper response from the server
        utc_time = datetime.utcfromtimestamp(ntp.request(ntp_server).tx_time) - timedelta(seconds=10)
        time_now  = "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(utc_time)
        time_past = "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(utc_time - timedelta(seconds=granularity*memory))

        print("PAST:" + time_past)
        print("NOW: " + time_now)
        

        # Read Data points from now to some time in the past 
        # Tick the strategy to deduce BUY and SELL signals
        df = xreader.read_gdaxdata(time_past, time_now, granularity, currency, True, False)
        strategy.tick(df)
        buy_sig  = strategy.buy_signal()
        sell_sig = strategy.sell_signal()

        # TODO: Position Open/Close Management

        print(df)
        time.sleep(granularity)

# Given a CSV file containing CryptoCurrency historic prices
# We emulate a Trading Run between the starting time and ending time of the timeseries
# And we iterate in a similar fashion as the real-time run
def run_backtest(xreader, strategy):
    global granularity
    global file

    # First and last from the file define when we start and when we stop
    ts_start    = xreader.get_gdaxcsv_timestamp(backtest_file_path, select='first')
    ts_end      = xreader.get_gdaxcsv_timestamp(backtest_file_path, select='last')

    # technically, if unable to open the file, just stop
    if ts_start == None or ts_end == None:
        print("ERROR occured, Returning")
        return

    gran = xreader.get_gdaxcsv_granularity(backtest_file_path)
    
    if gran != granularity:
        print("WARNING - Granularity found different in file than Initial value - File value is assumed: " + str(gran))
        granularity= gran

    start = datetime.fromtimestamp(ts_start)
    end   = datetime.fromtimestamp(ts_end)
    
    time_now = datetime.now()

    start_str = "{:%Y-%m-%dT%H:%M:%S}".format(start)  
    end_str   = "{:%Y-%m-%dT%H:%M:%S}".format(end)
    now_str   = "{:%Y-%m-%dT%Hh%Mm%Ss}".format(time_now)
    
    # open log file 
    target_folder = "log/"
    dir = os.path.dirname(target_folder)
    if not os.path.exists(dir):
        os.makedirs(dir)
    file = open("log/StrategyRun-" + now_str + ".txt", "w")
   
    LogPrint("STRATEGY RUN - CROSSING MA")
    LogPrint("GRANULARITY(S): " + str(granularity))
    LogPrint("MEMORY(S): " + str(memory))
    LogPrint("INITIAL INVESTMENT(EUR): " + str(investment))
    LogPrint("TRADED CURRENCY: " + currency)
    LogPrint("BACKTEST CSV FILE: " + backtest_file_path)
    LogPrint("START TIME: " + start_str)
    LogPrint("END TIME: " + end_str)
    LogPrint("----------------")

    mopool = mp.MoneyPool(currency, investment, log_file=file) # Init Money Pooler with our initial Investment 
    
    nb_winning = 0  # number of winning trades 
    nb_losing = 0   # number of losing trades
    prev_account  = investment
    
    while(start < end):
        # emulate current time as old time by X days from now
        # Note : Server always return +1 hour results from the request UTC time
        time_now  = "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(start) 
        time_past = "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(start - timedelta(seconds=granularity*memory))

        #print("PAST: " + "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(start - timedelta(seconds=granularity*memory)))
        #print("NOW: " + "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(start) )
        #print("\n")
        
        # get slice of data from the CSV file
        df = xreader.read_gdaxcsvdata(time_past, time_now, backtest_file_path)   
        
        # Sometimes we have empty chunks for timeperiods. just continue
        # Note : means the exchange from where we get data is closed during that time
        if df.empty:
            start = start + timedelta(seconds=granularity) # advance time
            continue
        
        # Continue if we don't get the number of points we request
        if len(df.index) != memory:
            start = start + timedelta(seconds=granularity) # advance time
            continue
  
        df = strategy.tick(df)
       # print(df)
        buy_sig  = strategy.buy_signal()
        sell_sig = strategy.sell_signal()

        current_value = float(df.iloc[0]['close']) # Current Crypto Price at Session Close 

        if sell_sig == stg.Signal.SELL_STONG:
            if mopool.get_quantity() != 0.0:
                LogPrint(time_now)
                
                if current_value - prev_buy_value > 0:
                    nb_winning = nb_winning + 1
                else:
                    nb_losing = nb_losing + 1
                
                mopool.sell_order(mopool.get_quantity(), current_value, True) # sell all

                LogPrint("Gain: " + str(100*(mopool.get_account() - prev_account) / prev_account))
                LogPrint("-------------------")
                prev_account = mopool.get_account()
                

        elif buy_sig == stg.Signal.BUY_STONG:
            if mopool.get_account() > 0.0:
                LogPrint( "Time Now: " + time_now)
                prev_buy_value = float(df.iloc[0]['close'])
                mopool.buy_order(mopool.get_account(), current_value, True)
                LogPrint("-------------------")
        
        start = start + timedelta(seconds=granularity) # advance time
        #time.sleep(1)
    
    # sell all in the end
    if mopool.get_quantity() != 0.0:
        print(time_now)
        mopool.sell_order(mopool.get_quantity(), current_value, True) # sell all

    mopool.print_account()
    profit_ratio  = nb_winning/(nb_winning+nb_losing)
    LogPrint("Winning trades: " + str(nb_winning))
    LogPrint("Losing trades: " + str(nb_losing))
    LogPrint("Win Ratio: " + str(profit_ratio*100.0))

def main(argv):

    back_mode = False
   
    # Either we run in real-time mode with current market data feed 
    # or we can force a back-test mode where we give the algorithm the number of days 
    # in the past where it should start 

    if len(argv) == 0:
        LogPrint("Trader Started Running in Real-Time Mode\n")
    elif len(argv) !=1:
        LogPrint("Usage : Start without Args for Real-Time or -b for backtesting for a number of previous days\n")
        sys.exit(2)
    elif argv[0] !='-b':
        LogPrint("Usage : Start without Args for Real-Time or -b  for backtesting for a number of previous days\n")
        sys.exit(2)
    else:
        back_mode = True

    xreader = xr.XChangeReader()                    # init Exchange Data Reader
    strategy = stg.Strategy(currency, granularity)  # init strategy with the target currency

    if not back_mode:
        run_realtime(xreader,strategy)
    else:
        run_backtest(xreader,strategy)

    

   # file = open("log/" + currency + str(granularity) + "- " + str(day_start) + " to " + str(day_end) + ".txt", "w")
   # file.close()

if __name__ == "__main__":
    main(sys.argv[1:])