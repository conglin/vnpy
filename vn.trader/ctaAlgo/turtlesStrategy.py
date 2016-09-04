# encoding: UTF-8
import numpy as np
import talib
import math
import logging
from ctaBase import *
from ctaTemplate import CtaTemplate

class Portfolio(object):
    portfolio_value = 0
    cash = 100000
    positions = []
    marketValue = 300
    

class TradeContext(object):
    portfolio = Portfolio()
    tradedayNum = 0
    unit = 0
    atr = 0
    tradingSignal = 'start' 
    preTradingSignal = ''
    units_hold_max = 4
    units_hold = 0
    quantity = 0
    max_add = 0
    firstOpenPrice = 0
    s = 'IF0000'
    openObserveTime = 55;
    closeObserveTime = 20;
    atrTime = 20;

class TurtleOriginalStrategy(CtaTemplate):
    className = 'TalibDoubleSmaDemo'
    author = u'woods'

    # 策略参数
    initDays = 10        # 初始化数据所用的天数

    # 策略变量
    bar = None
    barMinute = EMPTY_STRING

    closeHistory = []       # 缓存K线收盘价的数组
    maxHistory = 10 * 10         # 最大缓存数量




    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol'
                 ]

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos'
               ]
    
    # tradedayNum = 0
    # unit = 0
    # atr = 0
    # tradingSignal = "start"
    # preTradingSignal = ""
    # units_hold_max = 4
    # units_hold = 0
    # quantity = 0
    # max_add = 0
    # firstOpenPrice = 0


    def getExtremem(self, arrayHighPriceResult, arrayLowPriceResult):
        np_arrayHighPriceResult = np.array(arrayHighPriceResult[:-1])
        np_arrayLowPriceResult = np.array(arrayLowPriceResult[:-1])
        maxResult = np_arrayHighPriceResult.max()
        minResult = np_arrayLowPriceResult.min()
        return [maxResult, minResult]
    
    def getAtrAndUnit(self, atrArrayResult, atrLengthResult, portfolioValueResult):
        atr = atrArrayResult[atrLengthResult-1]
        unit = math.floor(portfolioValueResult * .01 / atr)
        return [atr, unit]
    
    def getStopPrice(self, firstOpenPriceResult, units_hold_result, atrResult):
        stopPrice =  firstOpenPriceResult - 2*atrResult + (units_hold_result-1)*0.5*atrResult
        return stopPrice


    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(TurtleOriginalStrategy, self).__init__(ctaEngine, setting)
        
    
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'海龟演示策略初始化')
        self.context = TradeContext()
        self.context.tradedayNum = 0
        self.context.unit = 0
        self.context.atr = 0
        self.context.tradingSignal = 'start' 
        self.context.preTradingSignal = ''
        self.context.units_hold_max = 4
        self.context.units_hold = 0
        self.context.quantity = 0
        self.context.max_add = 0
        self.context.firstOpenPrice = 0
        self.context.s = 'IF0000'
        # update_universe([context.s])
        self.context.openObserveTime = 55;
        self.context.closeObserveTime = 20;
        self.context.atrTime = 20;

        initData = self.loadBar(self.initDays)
        for bar in initData:
            self.onBar(bar)

        self.putEvent()
    
    # ----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'海龟演示策略启动')
        self.putEvent()

    # ----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'海龟演示策略停止')
        self.putEvent()
        
        
        
    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        # 计算K线
        tickMinute = tick.datetime.minute

        if tickMinute != self.barMinute:
            if self.bar:
                self.onBar(self.bar)

            bar = CtaBarData()
            bar.vtSymbol = tick.vtSymbol
            bar.symbol = tick.symbol
            bar.exchange = tick.exchange

            bar.open = tick.lastPrice
            bar.high = tick.lastPrice
            bar.low = tick.lastPrice
            bar.close = tick.lastPrice

            bar.date = tick.date
            bar.time = tick.time
            bar.datetime = tick.datetime  # K线的时间设为第一个Tick的时间

            # 实盘中用不到的数据可以选择不算，从而加快速度
            # bar.volume = tick.volume
            # bar.openInterest = tick.openInterest

            self.bar = bar  # 这种写法为了减少一层访问，加快速度
            self.barMinute = tickMinute  # 更新当前的分钟

        else:  # 否则继续累加新的K线
            bar = self.bar  # 写法同样为了加快速度

            bar.high = max(bar.high, tick.lastPrice)
            bar.low = min(bar.low, tick.lastPrice)
            bar.close = tick.lastPrice

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 把最新的收盘价缓存到列表中
        self.closeHistory.append(bar.close)

        # 检查列表长度，如果超过缓存上限则移除最老的数据
        # 这样是为了减少计算用的数据量，提高速度
        if len(self.closeHistory) > self.maxHistory:
            self.closeHistory.pop(0)
        else:
            # 如果小于缓存上限，则说明初始化数据尚未足够，不进行后续计算
            return

        # # 将缓存的收盘价数转化为numpy数组后，传入talib的函数SMA中计算
        # closeArray = np.array(self.closeHistory)
        # fastSMA = ta.SMA(closeArray, self.fastPeriod)
        # slowSMA = ta.SMA(closeArray, self.slowPeriod)
        #
        # # 读取当前K线和上一根K线的数值，用于判断均线交叉
        # self.fastMa0 = fastSMA[-1]
        # self.fastMa1 = fastSMA[-2]
        # self.slowMa0 = slowSMA[-1]
        # self.slowMa1 = slowSMA[-2]
        #
        # # 判断买卖
        # crossOver = self.fastMa0>self.slowMa0 and self.fastMa1<self.slowMa1     # 金叉上穿
        # crossBelow = self.fastMa0<self.slowMa0 and self.fastMa1>self.slowMa1    # 死叉下穿
        #
        # # 金叉和死叉的条件是互斥
        # if crossOver:
        #     # 如果金叉时手头没有持仓，则直接做多
        #     if self.pos == 0:
        #         self.buy(bar.close, 1)
        #     # 如果有空头持仓，则先平空，再做多
        #     elif self.pos < 0:
        #         self.cover(bar.close, 1)
        #         self.buy(bar.close, 1)
        # # 死叉和金叉相反
        # elif crossBelow:
        #     if self.pos == 0:
        #         self.short(bar.close, 1)
        #     elif self.pos > 0:
        #         self.sell(bar.close, 1)
        #         self.short(bar.close, 1)
        

        portfolioValue = self.context.portfolio.portfolio_value
        highPrice = history(self.context.openObserveTime+1, '1d', 'high')[self.context.s]
        lowPriceForAtr = history(self.context.openObserveTime+1, '1d', 'low')[self.context.s]
        lowPriceForExtremem = history(self.context.closeObserveTime+1, '1d', 'low')[self.context.s]
        closePrice = history(self.context.openObserveTime+2, '1d', 'close')[self.context.s]
        closePriceForAtr = closePrice[:-1]
    
        atrArray = talib.ATR(highPrice.values, lowPriceForAtr.values, closePriceForAtr.values, timeperiod=self.context.atrTime)
    
        maxx = self.getExtremem(highPrice.values, lowPriceForExtremem.values)[0]
        minn = self.getExtremem(highPrice.values, lowPriceForExtremem.values)[1]
        atr = atrArray[-2]
    

        if (self.context.tradingSignal != 'start'):
            if (self.context.units_hold != 0):
                self.context.max_add += 0.5 * self.getAtrAndUnit(atrArray, atrArray.size, portfolioValue)[0]
        else:
            self.context.max_add = bar_dict[self.context.s].last
        
    
        curPosition = self.context.portfolio.positions[self.context.s].quantity
        availableCash = self.context.portfolio.cash
        marketValue = self.context.portfolio.market_value
    
    
        if (curPosition > 0 and bar_dict[self.context.s].last < minn):
            self.context.tradingSignal = 'exit'
        else:
            if (curPosition > 0 and bar_dict[self.context.s].last < self.getStopPrice(self.context.firstOpenPrice, self.context.units_hold, atr)):
                self.context.tradingSignal = 'stop'
            else:
                if (bar_dict[self.context.s].last > self.context.max_add and self.context.units_hold != 0 and self.context.units_hold < self.context.units_hold_max and availableCash > bar_dict[self.context.s].last*self.context.unit):
                    self.context.tradingSignal = 'entry_add'
                else:
                    if (bar_dict[self.context.s].last > maxx and self.context.units_hold == 0):
                        self.context.max_add = bar_dict[self.context.s].last
                        self.context.tradingSignal = 'entry'
                    
                
        atr = self.getAtrAndUnit(atrArray, atrArray.size, portfolioValue)[0]
        if self.context.tradedayNum % 5 == 0:
            self.context.unit = self.getAtrAndUnit(atrArray, atrArray.size, portfolioValue)[1]
        self.context.tradedayNum += 1
        self.context.quantity = self.context.unit

        if (self.context.tradingSignal != self.context.preTradingSignal or (self.context.units_hold < self.context.units_hold_max and self.context.units_hold > 1) or self.context.tradingSignal == 'stop'):

            if self.context.tradingSignal == 'entry':
                self.context.quantity = self.context.unit
                if availableCash > bar_dict[self.context.s].last*self.context.quantity:
                    order_shares(self.context.s, self.context.quantity)
                    self.context.firstOpenPrice = bar_dict[self.context.s].last
                    self.context.units_hold = 1


            if self.context.tradingSignal == 'entry_add':
                self.context.quantity = self.context.unit
                order_shares(self.context.s, self.context.quantity)
                self.context.units_hold += 1


            if self.context.tradingSignal == 'stop':
                if (self.context.units_hold > 0):
                    order_shares(self.context.s, -self.context.quantity)
                    self.context.units_hold -= 1


            if self.context.tradingSignal == 'exit':
                if curPosition > 0:
                    order_shares(self.context.s, -curPosition)
                    self.context.units_hold = 0


        self.context.preTradingSignal = self.context.tradingSignal
        # 发出状态更新事件
        self.putEvent()
        
      
  
    # ----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass

    # ----------------------------------------------------------------------
    def onTrade(self, trade):
        """收到成交推送（必须由用户继承实现）"""
        # 对于无需做细粒度委托控制的策略，可以忽略onOrder
        pass
        
if __name__ == '__main__':
    # 提供直接双击回测的功能
    # 导入PyQt4的包是为了保证matplotlib使用PyQt4而不是PySide，防止初始化出错
    from ctaBacktesting import *
    from PyQt4 import QtCore, QtGui
    
    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20120101')
    
    # 设置产品相关参数
    engine.setSlippage(0.2)     # 股指1跳
    engine.setRate(0.3/10000)   # 万0.3
    engine.setSize(300)         # 股指合约大小        
    
    # 设置使用的历史数据库
    engine.setDatabase(MINUTE_DB_NAME, 'IF0000')
    
    # 在引擎中创建策略对象
    d = {'atrLength': 11}
    engine.initStrategy(TurtleOriginalStrategy, d)
    
    # 开始跑回测
    engine.runBacktesting()
    
    # 显示回测结果
    engine.showBacktestingResult()
    
    ## 跑优化
    #setting = OptimizationSetting()                 # 新建一个优化任务设置对象
    #setting.setOptimizeTarget('capital')            # 设置优化排序的目标是策略净盈利
    #setting.addParameter('atrLength', 11, 12, 1)    # 增加第一个优化参数atrLength，起始11，结束12，步进1
    #setting.addParameter('atrMa', 20, 30, 5)        # 增加第二个优化参数atrMa，起始20，结束30，步进1
    #engine.runOptimization(AtrRsiStrategy, setting) # 运行优化函数，自动输出结果