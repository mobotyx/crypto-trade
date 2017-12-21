from datetime import datetime, timedelta
import time
import pandas as pd
from dateutil import parser
from enum import Enum
import technical_indicators as ti

class Signal(Enum):
    NONE = 'NONE'
    BUY_WEAK = 'BUY_WEAK'
    BUY_STONG = 'BUY_STONG'
    SELL_WEAK = 'SELL_WEAK'
    SELL_STONG = 'SELL_STONG'

class Strategy:
    
    def __init__(self, currency, granulaity):
        self.__currency = currency
        self.__buy  = Signal.NONE
        self.__sell = Signal.NONE
        self.__granularity = granulaity
        self.__p_fast_ma = None
        self.__p_slow_ma = None
        self.__rsi_sig  = Signal.NONE
        self.__rsi_prev = None

    # use a fast and a slow moving MA to determine 
    # if trend is going upward or downward based 
    # on both MA cross-over
    def ma_crossover(self, df):
        sig = Signal.NONE
        n  = len(df.index)
        name1='MA_{n}'.format(n=n)
        name2='MA_{n}'.format(n=int(n/2))
        df=ti.MA(df,int(n/2), col_name=name2)  # fast moving average
        df=ti.MA(df,n, col_name=name1)    # slow moving average

        curr_slow = df.iloc[n-1][name1]
        curr_fast = df.iloc[n-1][name2]

        # analyse MA crossover
        if self.__p_fast_ma != None and self.__p_slow_ma != None:
            if self.__p_fast_ma < self.__p_slow_ma and curr_fast > curr_slow:
                sig = Signal.BUY_STONG
                print("MA - Crossover: " + name1 + ', ' + name2 + ' UP')
            elif self.__p_fast_ma > self.__p_slow_ma and curr_fast < curr_slow:
                sig = Signal.SELL_STONG
                print("MA - Crossover: " + name1 + ', ' + name2 + ' DN')
            else:
                sig = Signal.NONE

        self.__p_fast_ma = curr_fast
        self.__p_slow_ma = curr_slow

        return df, sig

    # regularly determine if we are Bullish or 
    # Bearish using the RSI signal
    # NOTE: Does not to seem promising
    def rsi_bull_bear(self, df):
        n  = len(df.index)
        name= 'RSI_' + str(n)
        df = ti.RSI(df, n, name)
        #print(df)
        if self.__rsi_prev == None:
            self.__rsi_prev = df.iloc[n-1][name]
            return df

        #print(df.iloc[n-1][name])
        #print(self.__rsi_prev)
        # oversol signal 
        #if df.iloc[n-1][name] <= 0.4 and df.iloc[n-1][name] > 0.0 and df.iloc[n-1][name] > self.__rsi_prev:
        if  df.iloc[n-1][name] > 0.1 and df.iloc[n-1][name] < 0.9:
            self.__rsi_sig = Signal.BUY_STONG
            #print("RSI - Oversold")
        # overbought signal
        #elif df.iloc[n-1][name] < 1.0 and df.iloc[n-1][name] >= 0.6 and df.iloc[n-1][name] < self.__rsi_prev:
        else:
            self.__rsi_sig = Signal.SELL_STONG
            #print("RSI - OverBought")

        self.__rsi_prev = df.iloc[n-1][name]

        return df
        

    def tick(self, df):
        
        ## what the MA crossover is telling us
        df, sig0 = self.ma_crossover(df)
        df  = self.rsi_bull_bear(df)
       
        ## MA Crossover Strategy 
        if sig0 == Signal.BUY_STONG:
            self.__buy  = sig0
            self.__sell = Signal.NONE
        elif sig0 == Signal.SELL_STONG:
            self.__buy  = Signal.NONE
            self.__sell = sig0
        else:
            self.__buy  = Signal.NONE
            self.__sell  = Signal.NONE

        return df

    def volume_indicator():
        pass

    def buy_signal(self):
        return self.__buy

    def sell_signal(self): 
        return self.__sell
