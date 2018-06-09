# encoding: UTF-8

"""
Turtle交易策略
"""

from datetime import time

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import CtaTemplate, BarGenerator

import numpy as np
import talib
import math


def get_extreme(array_high_price_result, array_low_price_result):
    np_array_high_price_result = np.array(array_high_price_result[:-1])
    np_array_low_price_result = np.array(array_low_price_result[:-1])
    max_result = np_array_high_price_result.max()
    min_result = np_array_low_price_result.min()
    return [max_result, min_result]


def get_atr_and_unit(atr_array_result, atr_length_result, portfolio_value_result):
    atr =  atr_array_result[atr_length_result-1]
    unit = math.floor(portfolio_value_result * .01 / atr)
    return [atr, unit]


def get_stop_price(first_open_price_result, units_hold_result, atr_result):
    stop_price = first_open_price_result - 2 * atr_result + (units_hold_result - 1) * 0.5 * atr_result
    return stop_price


########################################################################
class TurtleStrategy(CtaTemplate):
    """海龟交易策略"""
    className = 'TurtleStrategy'
    author = u'Lin'

    # 策略参数
    fixedSize = 100
    k1 = 0.4
    k2 = 0.6

    initDays = 10

    策略变量
    barList = []                # K线对象的列表

    dayOpen = 0
    dayHigh = 0
    dayLow = 0

    range = 0
    longEntry = 0
    shortEntry = 0
    exitTime = time(hour=14, minute=55)

    longEntered = False
    shortEntered = False

    # 参数列表，保存了参数的名称
    paramList = [
                 'name',
                 'className',
                 'author',
                 'vtSymbol',
                 'k1',
                 'k2'
                ]    

    # 变量列表，保存了变量的名称
    varList = [
               'inited',
               'trading',
               'pos',
               'range',
               'longEntry',
               'shortEntry',
               'exitTime'
              ] 
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']    

    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(DualThrustStrategy, self).__init__(ctaEngine, setting) 
        
        self.bg = BarGenerator(self.onBar)
        self.barList = []
        
        self.context = {}
        self.context['trade_day_num'] = 0
        self.context['unit'] = 0
        self.context['atr'] = 0
        self.context['trading_signal'] = 'start'
        self.context['pre_trading_signal'] = ''
        self.context['units_hold_max'] = 4
        self.context['units_hold'] = 0
        self.context['quantity'] = 0
        self.context['max_add'] = 0
        self.context['first_open_price'] = 0
        self.context['s'] = '000300.XSHG'
        self.context['open_observe_time'] = 55
        self.context['close_observe_time'] = 20
        self.context['atr_time'] = 20

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)
    
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单）
        self.cancelAll()

        # 计算指标数值
        self.barList.append(bar)
        
        if len(self.barList) <= 2:
            return
        else:
            self.barList.pop(0)
        lastBar = self.barList[-2]
        
        # 新的一天
        if lastBar.datetime.date() != bar.datetime.date():
            # 如果已经初始化
            if self.dayHigh:
                self.range = self.dayHigh - self.dayLow
                self.longEntry = bar.open + self.k1 * self.range
                self.shortEntry = bar.open - self.k2 * self.range           
                
            self.dayOpen = bar.open
            self.dayHigh = bar.high
            self.dayLow = bar.low

            self.longEntered = False
            self.shortEntered = False
        else:
            self.dayHigh = max(self.dayHigh, bar.high)
            self.dayLow = min(self.dayLow, bar.low)

        # 尚未到收盘
        if not self.range:
            return

        if bar.datetime.time() < self.exitTime:
            # if self.pos == 0:
            #     if bar.close > self.dayOpen:
            #         if not self.longEntered:
            #             self.buy(self.longEntry, self.fixedSize, stop=True)
            #     else:
            #         if not self.shortEntered:
            #             self.short(self.shortEntry, self.fixedSize, stop=True)
            #
            # # 持有多头仓位
            # elif self.pos > 0:
            #     self.longEntered = True
            #
            #     # 多头止损单
            #     self.sell(self.shortEntry, self.fixedSize, stop=True)
            #
            #     # 空头开仓单
            #     if not self.shortEntered:
            #         self.short(self.shortEntry, self.fixedSize, stop=True)
            #
            # # 持有空头仓位
            # elif self.pos < 0:
            #     self.shortEntered = True
            #
            #     # 空头止损单
            #     self.cover(self.longEntry, self.fixedSize, stop=True)
            #
            #     # 多头开仓单
            #     if not self.longEntered:
            #         self.buy(self.longEntry, self.fixedSize, stop=True)
            portfolio_value = self.context['portfolio']['portfolio_value']
            high_price = history_bars(self.context.s, self.context.open_observe_time + 1, '1d', 'high')
            low_price_for_atr = history_bars(self.context.s, self.context.open_observe_time + 1, '1d', 'low')
            low_price_for_extreme = history_bars(self.context.s, self.context.close_observe_time + 1, '1d', 'low')
            close_price = history_bars(self.context.s, self.context.open_observe_time + 2, '1d', 'close')
            close_price_for_atr = close_price[:-1]

            atr_array = talib.ATR(high_price, low_price_for_atr, close_price_for_atr, timeperiod=self.context.atr_time)

            maxx = get_extreme(high_price, low_price_for_extreme)[0]
            minn = get_extreme(high_price, low_price_for_extreme)[1]
            atr = atr_array[-2]

            if self.context.trading_signal != 'start':
                if self.context.units_hold != 0:
                    self.context.max_add += 0.5 * get_atr_and_unit(atr_array, atr_array.size, portfolio_value)[0]
            else:
                self.context.max_add = bar_dict[self.context.s].last
            cur_position = self.context.portfolio.positions[self.context.s]
            cur_position = cur_position.quantity if cur_position else 0
            available_cash = self.context.portfolio.cash
            market_value = self.context.portfolio.market_value

            if (cur_position > 0 and
                    bar_dict[self.context.s].last < get_stop_price(self.context.first_open_price, self.context.units_hold, atr)):
                self.context.trading_signal = 'stop'
            else:
                if cur_position > 0 and bar_dict[self.context.s].last < minn:
                    self.context.trading_signal = 'exit'
                else:
                    if (bar_dict[self.context.s].last > self.context.max_add and self.context.units_hold != 0 and
                            self.context.units_hold < self.context.units_hold_max and
                            available_cash > bar_dict[self.context.s].last*self.context.unit):
                        self.context.trading_signal = 'entry_add'
                    else:
                        if bar_dict[self.context.s].last > maxx and self.context.units_hold == 0:
                            self.context.max_add = bar_dict[self.context.s].last
                            self.context.trading_signal = 'entry'

            atr = get_atr_and_unit(atr_array, atr_array.size, portfolio_value)[0]
            if self.context.trade_day_num % 5 == 0:
                self.context.unit = get_atr_and_unit(atr_array, atr_array.size, portfolio_value)[1]
            self.context.trade_day_num += 1
            self.context.quantity = self.context.unit

            if (self.context.trading_signal != self.context.pre_trading_signal or
                    (self.context.units_hold < self.context.units_hold_max and self.context.units_hold > 1) or
                    self.context.trading_signal == 'stop'):
                if self.context.trading_signal == 'entry':
                    self.context.quantity = self.context.unit
                    if available_cash > bar_dict[self.context.s].last*self.context.quantity:
                        order_shares(self.context.s, self.context.quantity)
                        self.context.first_open_price = bar_dict[self.context.s].last
                        self.context.units_hold = 1

                if self.context.trading_signal == 'entry_add':
                    self.context.quantity = self.context.unit
                    order_shares(self.context.s, self.context.quantity)
                    self.context.units_hold += 1

                if self.context.trading_signal == 'stop':
                    if self.context.units_hold > 0:
                        order_shares(self.context.s, -self.context.quantity)
                        self.context.units_hold -= 1

                if self.context.trading_signal == 'exit':
                    if cur_position > 0:
                        order_shares(self.context.s, -cur_position)
                        self.context.units_hold = 0
            
        # 收盘平仓
        else:
            if self.pos > 0:
                self.sell(bar.close * 0.99, abs(self.pos))
            elif self.pos < 0:
                self.cover(bar.close * 1.01, abs(self.pos))
 
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass
        

##############
# from rqalpha.api import *






def handle_bar(context, bar_dict):
    portfolio_value = context.portfolio.portfolio_value
    high_price = history_bars(context.s, context.open_observe_time + 1, '1d', 'high')
    low_price_for_atr = history_bars(context.s, context.open_observe_time + 1, '1d', 'low')
    low_price_for_extreme = history_bars(context.s, context.close_observe_time + 1, '1d', 'low')
    close_price = history_bars(context.s, context.open_observe_time + 2, '1d', 'close')
    close_price_for_atr = close_price[:-1]

    atr_array = talib.ATR(high_price, low_price_for_atr, close_price_for_atr, timeperiod=context.atr_time)

    maxx = get_extreme(high_price, low_price_for_extreme)[0]
    minn = get_extreme(high_price, low_price_for_extreme)[1]
    atr = atr_array[-2]

    if context.trading_signal != 'start':
        if context.units_hold != 0:
            context.max_add += 0.5 * get_atr_and_unit(atr_array, atr_array.size, portfolio_value)[0]
    else:
        context.max_add = bar_dict[context.s].last
    cur_position = context.portfolio.positions[context.s]
    cur_position = cur_position.quantity if cur_position else 0
    available_cash = context.portfolio.cash
    market_value = context.portfolio.market_value

    if (cur_position > 0 and
            bar_dict[context.s].last < get_stop_price(context.first_open_price, context.units_hold, atr)):
        context.trading_signal = 'stop'
    else:
        if cur_position > 0 and bar_dict[context.s].last < minn:
            context.trading_signal = 'exit'
        else:
            if (bar_dict[context.s].last > context.max_add and context.units_hold != 0 and
                    context.units_hold < context.units_hold_max and
                    available_cash > bar_dict[context.s].last*context.unit):
                context.trading_signal = 'entry_add'
            else:
                if bar_dict[context.s].last > maxx and context.units_hold == 0:
                    context.max_add = bar_dict[context.s].last
                    context.trading_signal = 'entry'

    atr = get_atr_and_unit(atr_array, atr_array.size, portfolio_value)[0]
    if context.trade_day_num % 5 == 0:
        context.unit = get_atr_and_unit(atr_array, atr_array.size, portfolio_value)[1]
    context.trade_day_num += 1
    context.quantity = context.unit

    if (context.trading_signal != context.pre_trading_signal or
            (context.units_hold < context.units_hold_max and context.units_hold > 1) or
            context.trading_signal == 'stop'):
        if context.trading_signal == 'entry':
            context.quantity = context.unit
            if available_cash > bar_dict[context.s].last*context.quantity:
                order_shares(context.s, context.quantity)
                context.first_open_price = bar_dict[context.s].last
                context.units_hold = 1

        if context.trading_signal == 'entry_add':
            context.quantity = context.unit
            order_shares(context.s, context.quantity)
            context.units_hold += 1

        if context.trading_signal == 'stop':
            if context.units_hold > 0:
                order_shares(context.s, -context.quantity)
                context.units_hold -= 1

        if context.trading_signal == 'exit':
            if cur_position > 0:
                order_shares(context.s, -cur_position)
                context.units_hold = 0

    context.pre_trading_signal = context.trading_signal