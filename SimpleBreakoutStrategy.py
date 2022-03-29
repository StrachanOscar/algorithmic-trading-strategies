'''
An algorithm that implements a simple breakout strategy.

Once an instrument's price exceeds previous historical highs over a dynamic lookback period, 
a buy order is executed and held until the price drops below a set risk threshold (stop loss).

The lookback period is dynamically determined by the instruments volatility.

A trailing stop loss rises with the price as it runs. 

Written by Oscar David Strachan on 29/03/22.
'''

import numpy as np

class SimpleBreakoutStrategy(QCAlgorithm):

    def Initialize(self):
        '''
        Initialising basics. Setting lookback parameters, stop-risk
        thresholds and a scheduled boot-up time for the algorithm.
        '''
        self.SetStartDate(2017, 3, 1)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        self.SetEndDate(2022, 3, 1)
        self.symbol = self.AddEquity("SPY", Resolution.Daily).Symbol
        
        self.lookback = 20
        self.ceiling, self.floor = 30, 10
        
        self.initialStopRisk = 0.98
        self.trailingStopRisk = 0.90
        
        self.Schedule.On(self.DateRules.EveryDay(self.symbol), \
                        self.TimeRules.AfterMarketOpen(self.symbol, 20), \
                        Action(self.EveryMarketOpen))

    def OnData(self, data: Slice):
        self.Plot("Data Chart", self.symbol, self.Securities[self.symbol].Close)
        

    def EveryMarketOpen(self):
        '''
        Calculates a 31-day delta volatility within set parameters.
        Resets the breakout level dynamically.
        '''
        # Calculating delta volatility and ensuring it falls within lookback parameters.
        close = self.History(self.symbol, 31, Resolution.Daily)["close"]
        todayvol = np.std(close[1:31])
        yesterdayvol = np.std(close[0:30])
        deltavol = (todayvol - yesterdayvol) / todayvol
        self.lookback = round(self.lookback * (1 + deltavol))
        
        if self.lookback > self.ceiling:
            self.lookback = self.ceiling
        elif self.lookback < self.floor:
            self.lookback = self.floor
            
        self.high = self.History(self.symbol, self.lookback, Resolution.Daily)["high"]
        
        # Investing upon breakout.
        if not self.Securities[self.symbol].Invested and \
                self.Securities[self.symbol].Close >= max(self.high[:-1]):
                
            self.SetHoldings(self.symbol, 1)
            self.breakoutlvl = max(self.high[:-1])
            self.highestPrice = self.breakoutlvl
            
        if self.Securities[self.symbol].Invested:
            # Setting our stop loss once invested.
            if not self.Transactions.GetOpenOrders(self.symbol):
                self.StopMarketTicket = self.StopMarketOrder(self.symbol, \
                                        -self.Portfolio[self.symbol].Quantity, \
                                        self.initialStopRisk * self.breakoutlvl)
            # Adjusting stop loss.                            
            if self.Securities[self.symbol].Close > self.highestPrice and \
                    self.initialStopRisk * self.breakoutlvl < self.Securities[self.symbol].Close * self.trailingStopRisk:
                self.highestPrice = self.Securities[self.symbol].Close
                updateFields = UpdateOrderFields()
                updateFields.StopPrice = self.Securities[self.symbol].Close * self.trailingStopRisk
                self.StopMarketTicket.Update(updateFields)
                
                self.Debug(updateFields.StopPrice)
                
            self.Plot("Data Chart", "Stop Price", self.StopMarketTicket.Get(OrderField.StopPrice))
            
            
            
    
        