# encoding: UTF-8
from datetime import time

from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import CtaTemplate, BarGenerator, ArrayManager

import numpy as np
import talib
import math

class DONCHIAN_strategy(CtaTemplate):

    className = 'DONCHIAN_strategy'
    author = u'尔鸫' 

    # 策略参数，添加需要的参数
                     
    init_days = 351                       
    ma_350 = 350
    ma_25 = 25
    enter_window = 20
    out_window = 10 
    atr_window = 20
    stop_loss_multiper = 2
    capital_size = 160000
    size = 10

     
    # 策略变量，添加需要的变量
    
    position_size = 0
    atr_value = 0
    ma_350_value = 0
    ma_25_value = 0
    max_value_enter = 0
    min_value_enter = 0
    max_value_out = 0
    min_value_out = 0
    open_price = 0
    open_price_list = []
    close_price_list = []
    pos_list = []

    
    
    # 参数列表
    paramList = ['name',
                 'className',
                 'author',
                 'vtSymbol',
                 'ma_350',
                 'ma_25',
                 'init_days',
                 'stop_loss_multiper',
                 'atr_window',
                 'capital_size',
                 'out_window',
                 'enter_window',
                 'size'
                 ]

    # 变量列表
    varList = ['inited',
               'trading',
               'pos',
               'position_size',
               'atr_value',
               'ma_350_value',
               'ma_25_value',
               'max_value_enter',
               'min_value_enter',
               'max_value_out',
               'min_value_out',
               'open_price',
               'pos_list',
               'close_price_list',
               'open_price_list'
               ]


    #----------------------------------------------------------------------
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(DONCHIAN_strategy, self).__init__(ctaEngine, setting)
        
        self.bm = BarGenerator(self.onBar, xmin=0, onXminBar=None)        
        
        self.am = ArrayManager(351)
        
    #----------------------------------------------------------------------
    def onInit(self): 
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)
        
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        initData = self.loadBar(self.init_days)
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
        self.bm.updateTick(tick)



    #----------------------------------------------------------------------
    def onBar(self, bar):

    	# 全撤之前发出的委托
        self.cancelAll()

         # 保存K线数据
        am = self.am
        
        am.updateBar(bar)
        
        if not am.inited:
            return
        
        # 计算指标数值
        self.ma_350_value = am.sma(self.ma_350)
        self.ma_25_value = am.sma(self.ma_25)
        self.atr_value = am.atr(self.atr_window)
        self.max_value_enter, self.min_value_enter = am.donchian(self.enter_window)
        self.max_value_out, self.min_value_out = am.donchian(self.out_window)


        
        self.pos_list.append(abs(self.pos))
        if len(self.pos_list) > 2 and self.pos_list[-2] != 0 and self.pos_list[-1] == 0:
            #print(self.open_price_list[-1],self.close_price_list[-1])
            self.capital_size = self.capital_size + \
                            self.pos_list[-2]*self.size*(self.open_price_list[-1]+self.close_price_list[-1])


        if self.pos == 0:

            self.position_size = math.floor(self.capital_size*0.01/self.atr_value)
            if self.position_size <= 0:
                self.position_size = 0
            if self.ma_25_value > self.ma_350_value:
                self.buy(self.max_value_enter, self.position_size, True)
                self.open_price = self.max_value_enter
                self.open_price_list.append(-1*self.max_value_enter)
                #print(self.position_size)
            elif self.ma_25_value < self.ma_350_value:
                self.short(self.min_value_enter, self.position_size, True)
                #print(self.position_size)
                self.open_price = self.min_value_enter
                self.open_price_list.append(self.min_value_enter)


        
        if self.pos > 0:
            #if self.ma_25_value < self.ma_350_value:
            if self.min_value_out > self.open_price-self.stop_loss_multiper*self.atr_value:
            	self.sell(self.min_value_out, abs(self.pos), True)
                self.close_price_list.append(self.min_value_out)
            else:
            	self.sell(self.open_price-self.stop_loss_multiper*self.atr_value, abs(self.pos), True)
                self.close_price_list.append(self.open_price-self.stop_loss_multiper*self.atr_value)
            #print(self.min_value_out,self.open_price-self.stop_loss_multiper*self.atr_value)
        elif self.pos < 0:
            
            #if self.ma_25_value > self.ma_350_value:
            if self.max_value_out < self.open_price+self.stop_loss_multiper*self.atr_value:
            	self.cover(self.max_value_out, abs(self.pos), True)
                self.close_price_list.append(-1*self.max_value_out)
            else:
            	self.cover(self.open_price+self.stop_loss_multiper*self.atr_value, abs(self.pos), True) 
                self.close_price_list.append(-1*(self.open_price+self.stop_loss_multiper*self.atr_value))
            #print(-1*self.max_value_out,-1*(self.open_price+self.stop_loss_multiper*self.atr_value))
            	

        self.putEvent()





    #----------------------------------------------------------------------
    def onXminbar(self, bar):

        pass




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




    #----------------------------------------------------------------------
    def customized_function(self, *args):

    	pass