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


    def ma_crossover(self, df):
        sig = Signal.NONE
        n  = len(df.index)
        name1='MA_{n}'.format(n=n)
        name2='MA_{n}'.format(n=int(n/2))
        df = ti.MA(df,int(n/2), col_name=name2)  # fast moving average
        df = ti.MA(df,n, col_name=name1)    # slow moving average
        
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

    
    def tick(self, df):
        
        ## what the MA crossover is telling us
        df, sig = self.ma_crossover(df)
       
        ## MA Crossover Strategy 
        if sig == Signal.BUY_STONG:
            self.__buy  = sig
            self.__sell = Signal.NONE
        elif sig == Signal.SELL_STONG:
            self.__buy  = Signal.NONE
            self.__sell = sig
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
