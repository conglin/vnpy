//https://www.ricequant.com/community/topic/62/%E8%B6%8B%E5%8A%BF%E7%AD%96%E7%95%A5%E5%B0%8F%E8%AF%95%E7%89%9B%E5%88%80-%E6%B5%B7%E9%BE%9F%E4%BA%A4%E6%98%93%E4%BD%93%E7%B3%BB%E7%9A%84%E5%B0%8F%E7%99%BD%E6%9E%84%E5%BB%BA/7
public class TurtleOriginalStrategy implements IHStrategy {
  Core talibCore;

//定义全局变量
  static int tradedayNum = 0;
  static double unit = 0;
  static double atr = 0;
  static String tradingSignal = "start";
  static String preTradingSignal = "";
  static int units_hold_max = 4;
  static int units_hold = 0;
  static double quantity = 0;
  static double max_add = 0;
  static double firstOpenPrice = 0;
  
  //计算最大最小值
  public double[] getExtremem(double[] arrayHighPriceResult, double[] arrayLowPriceResult) {
      DescriptiveStatistics forMax = new DescriptiveStatistics();
      for (int i = 0; i < arrayHighPriceResult.length-1; i++) {
          forMax.addValue(arrayHighPriceResult[i]);
      }
      double maxResult = forMax.getMax();
      
      DescriptiveStatistics forMin = new DescriptiveStatistics();
      for (int i = 0; i < arrayLowPriceResult.length-1; i++) {
          forMin.addValue(arrayLowPriceResult[i]);
      }
      double minResult = forMin.getMin();
      
      double[] forExtremum = new double[2];
      forExtremum[0] = maxResult;
      forExtremum[1] = minResult;
      return forExtremum;
  }
  //计算Atr以及单位
  public double[] getAtrAndUnit(double[] atrArrayResult, MInteger atrLengthResult, double portfolioValueResult) {
      double atr = atrArrayResult[atrLengthResult.value-1];
      double unit = Math.floor(portfolioValueResult * .01 / atr);
      double[] atrAndUnit = new double[2];
      atrAndUnit[0] = atr;
      atrAndUnit[1] = unit;
      return atrAndUnit;
  }
  //计算止损线价位
  public double getStopPrice(double firstOpenPriceResult, int units_hold_result, double atrResult) {
      double stopPrice =  firstOpenPriceResult - 2*atrResult + (units_hold_result-1)*0.5*atrResult;
      return stopPrice;
  }
  
  
 
  @Override
  public void init(IHInformer informer, IHInitializers initializers) {
    
    talibCore = new Core();
    
    
    int openObserveTime = 55;
    int closeObserveTime = 20;
    int atrTime = 20;
    MInteger atrBegin = new MInteger();
    MInteger atrLength = new MInteger();

    
    String stockId = "CSI300.INDX";
    initializers.instruments((universe) -> universe.add(stockId));
    
    
    initializers.events().statistics((stats, info, trans) -> {

        //获取组合总价值，包含市场价值与剩余资金
        double portfolioValue = info.portfolio().getPortfolioValue();
        
        
        double[] highPrice = stats.get(stockId).history(openObserveTime+1, HPeriod.Day).getHighPrice();
        double[] lowPriceForAtr = stats.get(stockId).history(openObserveTime+1, HPeriod.Day).getLowPrice();
        double[] lowPriceForExtremem = stats.get(stockId).history(closeObserveTime+1, HPeriod.Day).getLowPrice();
        double[] closePrice = stats.get(stockId).history(openObserveTime+2, HPeriod.Day).getClosingPrice();
        
        double closePriceForAtr[] = new double[closePrice.length-1];
        for (int i = 0; i < closePrice.length-1; i++) {
            closePriceForAtr[i] = closePrice[i];
        }
        
       
        double[] atrArray = new double[openObserveTime];
        //Talib计算N即ATR
        RetCode retCode = talibCore.atr(0, openObserveTime-1, highPrice, lowPriceForAtr, closePriceForAtr, atrTime, atrBegin, atrLength, atrArray);
        
        
        double max = getExtremem(highPrice, lowPriceForExtremem)[0];
        double min = getExtremem(highPrice, lowPriceForExtremem)[1];
        
        
        double atr = atrArray[atrLength.value-1];
        
        if (tradingSignal != "start") {
            if (units_hold != 0) {
            max_add += 0.5 * getAtrAndUnit(atrArray, atrLength, portfolioValue)[0];
            }
        } else {
            max_add = stats.get(stockId).getLastPrice();
        }
        
        informer.info(units_hold);
        
        double curPosition = info.position(stockId).getNonClosedTradeQuantity();
        double availableCash = info.portfolio().getAvailableCash();
        double marketValue = info.portfolio().getMarketValue();
        
        
        if (curPosition > 0 & stats.get(stockId).getLastPrice() < getStopPrice(firstOpenPrice, units_hold, atr)) {
            tradingSignal = "stop";
        } else {
            if (curPosition > 0 & stats.get(stockId).getLastPrice() < min) {
                tradingSignal = "exit";
            } else {
                if (stats.get(stockId).getLastPrice() > max_add & units_hold != 0 & units_hold < units_hold_max & availableCash > stats.get(stockId).getLastPrice()*unit) {
                    tradingSignal = "entry_add";
                } else {
                    if (stats.get(stockId).getLastPrice() > max & units_hold == 0) {
                        max_add = stats.get(stockId).getLastPrice();
                        tradingSignal = "entry";
                    }
                }
            }
        }
        
        //informer.info(tradingSignal);
        
        atr = getAtrAndUnit(atrArray, atrLength, portfolioValue)[0];
        if (tradedayNum % 5 == 0) {
            unit = getAtrAndUnit(atrArray, atrLength, portfolioValue)[1];
        }
        tradedayNum += 1;
        
        double quantity = unit;
        
        
        if (tradingSignal != preTradingSignal | (units_hold < units_hold_max & units_hold > 1) | tradingSignal == "stop") {
            
            
            if (tradingSignal == "entry") {
                quantity = unit;
                if (availableCash > stats.get(stockId).getLastPrice()*quantity) {
                    trans.buy(stockId).shares(quantity).commit();
                    firstOpenPrice = stats.get(stockId).getLastPrice();
                    units_hold = 1;
                    informer.info("entrybuy" + quantity);
                }
            }
            if (tradingSignal == "entry_add") {
                quantity = unit;
                trans.buy(stockId).shares(quantity).commit();
                units_hold += 1;
                informer.info("entry_addbuy" + quantity);
            }
            
            
            if (tradingSignal == "stop") {
                if (/*curPosition marketValue*/ units_hold > 0) {
                    trans.sell(stockId).shares(quantity).commit();
                    units_hold -= 1;
                    informer.info("stop" + quantity);
                }
            }
            if (tradingSignal == "exit") {
                if (curPosition > 0) {
                    trans.sell(stockId).shares(curPosition).commit();
                    units_hold = 0;
                    informer.info("exitsell" + curPosition);
                }
            }
            
        }
        
        preTradingSignal = tradingSignal;
    
    });
      
  }
}