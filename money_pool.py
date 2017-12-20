
from enum import Enum
# __slots : how we are distributing the money at hand (not invested)

class OrderResult(Enum):
    INSUFFICIENT = 0    # insufficient balance
    PLACED = 1          # order placed    

# for now we emulate account value and amounts locally 
# typically, this information is requested/updated from the Xchange server

class MoneyPool:
    def __init__(self, currency, account_value, quantity_value=0, transact_fee=0.0025):
        self.__account   = account_value    # money at Hand or avail for investment
        self.__quantity  = quantity_value   # current quantity of cryptomoney                   
        self.__fee       = transact_fee     # Transaction fee 
        self.__currency  = currency         # Currency Identify ex. 'LTC-EUR'

    # Returns the current account level (money at hand)
    def get_account(self):
        return self.__account 


    # Returns the current crypto quantity we own in the market
    def get_quantity(self):
        return self.__quantity


    # Emulate a buy order 
    def buy_order(self, amount_money, current_value, print_order = False):
        if self.__account < amount_money:
            if print_order:
                print("Buy Order failed, Requested: " + str(amount_money) + " Have: " + str(self.__account))
            return OrderResult.INSUFFICIENT

        if print_order:
            print("BUY ORDER")
            print("Crypto Price @: " + str(current_value))
            print("Account Before: " + str(self.__account))

        self.__account  = self.__account - amount_money
        self.__quantity = self.__quantity + amount_money*(1 - self.__fee)/current_value

        if print_order:
            print("Account After: " + str(self.__account))
            print("Updated Quantity: " + str(self.__quantity))
            print("-------------------")

        return OrderResult.PLACED


    # Emulate a sell order 
    def sell_order(self, quantity, current_value, print_order = False):
        if self.__quantity < quantity or self.__quantity == 0.0:
            print("Sell Order failed, Requested: " + str(quantity) + " Have: " + str(self.__quantity))
            return OrderResult.INSUFFICIENT

        if print_order:
            print("SELL ORDER")
            print("Crypto Price @: " + str(current_value))
            print("Account Before: " + str(self.__account))

        self.__quantity = self.__quantity - quantity
        self.__account  = self.__account + quantity*current_value*(1 - self.__fee)
        
        if print_order:
            print("Account After: " + str(self.__account))
            print("Updated Quantity: " + str(self.__quantity))
            print("-------------------")

        return OrderResult.PLACED


    def print_account(self, file = None):
        print("Acccount Information - " + str(self.__currency))
        print("Crypto Quantity:  " + str(self.__quantity))
        print("Account Value:  " + str(self.__account))

        if file !=None:
            pass # write to file
            
