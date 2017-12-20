from datetime import datetime, timedelta
import time
import pandas as pd
from dateutil import parser
from enum import Enum

class Signal(Enum):
    NONE = 'NONE'
    WEAK = 'WEAK'
    STONG = 'STONG'


class Strategy:
    
    def __init__(self, currency, granulaity):
        self.__currency = currency
        self.__buy  = Signal.NONE
        self.__sell = Signal.NONE
        self.__granularity = granulaity

    def tick(self, df):
        
        ## Simple strategy to start with 
        for i, (index, row) in enumerate(df.iterrows()):
            
            if row['RG'] == '':
                self.__buy = Signal.NONE
                self.__sell = Signal.NONE
            elif row['RG'] == 'GREEN':
                self.__buy = Signal.STONG
                self.__sell = Signal.NONE
            elif row['RG'] == 'RED':
                self.__buy = Signal.NONE
                self.__sell = Signal.STONG
     
            break

    def volume_indicator():
        pass

    def buy_signal(self):
        return self.__buy

    def sell_signal(self): 
        return self.__sell
