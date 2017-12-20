#!/usr/bin/python
import sys, getopt
from datetime import datetime, timedelta
import time
import pandas as pd
from dateutil import parser
import ntplib

import xchange_reader as xr
import strategy as stg
import money_pool as mp

file = None 
ntp_server = 'europe.pool.ntp.org'
investment = 1000                       # Initial Allocated budget
currency = 'LTC-EUR'                    # currency     
granularity = 600                       # resolution in seconds (datapoints spacing)
memory = 3                              # number of points into the past that the strategy uses

def LogPrint(str_line):
    print(str_line)
    file.write(str_line + '\n')

def add_datetime(time_info):
    return parser.parse(time_info)


## BUY when the previous session close price is higher than open price 
## Money is pooled in chunks to average out wins vs losses 
## As long as there is money to invest and the bar is green, put the next chunk
## The first Red detected and take all the money out and assume the win or the loss
def strategy_1(df, invest = 1000, pools = [0.6,0.35,0.05], transaction_fee = 0.0025):
    
    LogPrint("STRATEGY #1-RUN - BUY WHEN A SESSION CLOSE PRICE IS HIGHER THAN OPEN @ CLOSE PRICE")
    LogPrint("POOL MONEY EVERY TIME A SESSION IS GREEN:" )

    for i in range(0, len(pools)):
        LogPrint("POOL #" + str(i) + " %" + str(pools[i]*100) + " Amount: " + str(pools[i]*invest))

    LogPrint("WHEN A SESSION CLOSE WITH A CLOSE PRICE LOWER THAN OPEN, SELL ALL @CLOSE PRICE AND WAIT FOR NEXT GREEN")

    pool_id = 0
    df['BUY-Amount'] = 0.0
    df['BUY-Qty']    = 0.0
    df['SELL-Amount'] = 0.0
    df['SELL-Qty']    = 0.0
    df['Account']     = 0.0
    df['Gain']        = 0.0
    
    total_qty = 0
    total_invested = 0

    for i, (index, row) in enumerate(df.iterrows()):

        if row['RG'] == '':
            continue

        if row['RG'] == 'GREEN' and pool_id < len(pools) and i < (len(df) - 1):

            buy_amount = invest*pools[pool_id] - transaction_fee*invest*pools[pool_id]

            df.loc[index, 'BUY-Amount'] = buy_amount
            df.loc[index, 'BUY-Qty']  = buy_amount/df.loc[index, 'close']
            total_qty = total_qty + buy_amount/df.loc[index, 'close']
            total_invested = total_invested + invest*pools[pool_id]
            pool_id = pool_id + 1
            
        elif row['RG'] == 'RED' or i == (len(df) - 1):
            df.loc[index, 'SELL-Qty'] = total_qty
            df.loc[index, 'SELL-Amount'] = total_qty * df.loc[index, 'close'] 
            df.loc[index, 'Account'] = total_qty * df.loc[index, 'close'] + invest - total_invested
            df.loc[index, 'Gain'] = df.loc[index, 'Account'] - invest 
            pool_id = 0
            total_qty = 0
            total_invested = 0


def run_realtime(xreader, strategy):
    ntp = ntplib.NTPClient() # to get UTC time
    while(True):
        # Get UTC time since this is the actual server time used
        # Go back some seconds back to get a proper response from the server
        utc_time = datetime.utcfromtimestamp(ntp.request(ntp_server).tx_time) - timedelta(seconds=10)
        time_now  = "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(utc_time)
        time_past = "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(utc_time - timedelta(seconds=granularity*memory))

        print(time_now)
        print(time_past)

        # Read Data points from now to some time in the past 
        # Tick the strategy to deduce BUY and SELL signals
        df = xreader.read_gdaxdata(time_past, time_now, granularity, currency, True, False)
        strategy.tick(df)
        buy_sig  = strategy.buy_signal()
        sell_sig = strategy.sell_signal()

        print(df)
        time.sleep(granularity)


def run_backtest(xreader, strategy, back_days):
    ntp = ntplib.NTPClient() # to get UTC time

    start = datetime.utcfromtimestamp(ntp.request(ntp_server).tx_time) - timedelta(days=back_days)
    end   = datetime.utcfromtimestamp(ntp.request(ntp_server).tx_time) # current UTC at start 

    mopool = mp.MoneyPool(currency, investment) # Init Money Pooler with our initial Investment 

    while(start < end):
        # emulate current time as old time by X days from now
        # Note : Server always return +1 hour results from the request UTC time
        time_now  = "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(start - timedelta(hours=1)) 
        time_past = "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(start - timedelta(hours=1, seconds=granularity*memory))

        print("PAST: " + "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(start - timedelta(seconds=granularity*memory)))
        print("NOW: " + "{:%Y-%m-%dT%H:%M:%S.000000Z}".format(start) )
        print("\n")
      
        df = xreader.read_gdaxdata(time_past, time_now, granularity, currency, True, True)    
        strategy.tick(df)

        buy_sig  = strategy.buy_signal()
        sell_sig = strategy.sell_signal()

        current_value = float(df.iloc[0]['close']) # Current Crypto Price at Session Close 

        if sell_sig == stg.Signal.STONG:

            if mopool.get_quantity() != 0.0:
                mopool.sell_order(mopool.get_quantity(), current_value, True) # sell all

        elif buy_sig == stg.Signal.STONG:
            if mopool.get_account() > 0.0:
                mopool.buy_order(mopool.get_account(), current_value, True)
        
        
        start = start + timedelta(seconds=granularity) # advance time
        time.sleep(5)
    
    # sell all in the end
    if mopool.get_quantity() != 0.0:
        mopool.sell_order(mopool.get_quantity(), current_value, True) # sell all

    mopool.print_account()

def main(argv):

    back_mode = False
    back_days = 0
   
    # Either we run in real-time mode with current market data feed 
    # or we can force a back-test mode where we give the algorithm the number of days 
    # in the past where it should start 

    if len(argv) == 0:
        print("Trader Started Running in Real-Time Mode\n")
    elif len(argv) !=2:
        print("Usage : Start without Args for Real-Time or -b <days> for backtesting for a number of previous days\n")
        sys.exit(2)
    elif argv[0] !='-b':
        print("Usage : Start without Args for Real-Time or -b <days> for backtesting for a number of previous days\n")
        sys.exit(2)
    else:
        back_mode = True
        back_days = int(argv[1])

    xreader = xr.XChangeReader()                    # init Exchange Data Reader
    strategy = stg.Strategy(currency, granularity)  # init strategy with the target currency

    if not back_mode:
        run_realtime(xreader,strategy)
    else:
        run_backtest(xreader,strategy, back_days)

    





    
   # file = open("log/" + currency + str(granularity) + "- " + str(day_start) + " to " + str(day_end) + ".txt", "w")
   # file.close()

if __name__ == "__main__":
    main(sys.argv[1:])