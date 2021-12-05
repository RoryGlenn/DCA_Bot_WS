"""tradingview.py - pulls data from tradingview.com to see which coins we should buy."""

from tradingview_ta                      import TA_Handler, Interval
from pprint                              import pprint
from kraken_enums import *
from util.globals                        import G
from my_sql                          import SQL


class TVData:
    SCREENER       = "crypto"
    EXCHANGE       = "kraken"
    RECOMMENDATION = "RECOMMENDATION"
    BUY            = "BUY"
    STRONG_BUY     = "STRONG_BUY"
    ALL_INTERVALS  = [
        Interval.INTERVAL_1_MINUTE, 
        Interval.INTERVAL_5_MINUTES, 
        Interval.INTERVAL_15_MINUTES, 
        Interval.INTERVAL_1_HOUR, 
        Interval.INTERVAL_2_HOURS,
        Interval.INTERVAL_4_HOURS,
        Interval.INTERVAL_1_DAY,
        Interval.INTERVAL_1_WEEK,
        Interval.INTERVAL_1_MONTH]
    SCALP_INTERVALS = [
        Interval.INTERVAL_1_MINUTE, 
        Interval.INTERVAL_5_MINUTES, 
        Interval.INTERVAL_15_MINUTES,
        Interval.INTERVAL_1_HOUR,
        Interval.INTERVAL_2_HOURS,
        Interval.INTERVAL_4_HOURS]


class TradingView():
    def __get_recommendation(self, symbol_pair: str, interval: str) -> list:
        """Get a recommendation (buy or sell) for the symbol."""
        try:
            symbol_data = TA_Handler(symbol=symbol_pair, screener=TVData.SCREENER, exchange=TVData.EXCHANGE, interval=interval)
            if symbol_data is not None and symbol_data.get_analysis() is not None:
                return symbol_data.get_analysis().summary[TVData.RECOMMENDATION]
        except Exception as e:
            G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
        return []

    def _is_buy(self, symbol_pair: str):
        """Get recommendations for all intervals in TVData. 
        Buy the coin if all intervals indicate a BUY or STRONG_BUY."""
        
        for interval in TVData.SCALP_INTERVALS:
            rec = self.__get_recommendation(symbol_pair, interval)
            if rec != TVData.BUY and rec != TVData.STRONG_BUY:
                return False
        return True

    def is_buy_long(self, symbol_pair: str) -> bool:
        """Get recommendations for all intervals in TVData. 
        Buy the coin if all intervals indicate a BUY or STRONG_BUY."""
        
        for interval in TVData.ALL_INTERVALS:
            rec = self.__get_recommendation(symbol_pair, interval)
            if rec != TVData.BUY and rec != TVData.STRONG_BUY:
                return False
        return True

    def is_strong_buy(self, symbol_pair: str) -> bool:
        for interval in TVData.SCALP_INTERVALS:
            recomendation = self.__get_recommendation(symbol_pair, interval)
            if recomendation != TVData.STRONG_BUY:
                return False
        return True

    def get_buy_set(self) -> set:
        """
        For every coin on the kraken exchange, 
        get the analysis to see which one is a buy according to the time intervals.
        
        """

        sql       = SQL()
        buy_set   = set()
        iteration = 1

        result_set = sql.con_query("SELECT symbol FROM kraken_coins")
        
        if result_set.rowcount > 0:
            symbol_list = result_set.fetchall()
            total       = len(symbol_list)
            
            for _tuple in symbol_list:
                symbol = _tuple[0]
                G.log.print_and_log(f"{iteration} of {total}: {symbol}")
                
                if symbol not in StableCoins.STABLE_COINS_LIST:
                    if self._is_buy(symbol + StableCoins.USD):
                        buy_set.add(symbol)
                iteration+=1
        return buy_set

    def get_buy_long_set(self) -> set:
        """
        For every coin on the kraken exchange, 
        get the analysis to see which one is a buy according to the time intervals.
        
        """
        sql       = SQL()
        buy_set   = set()
        iteration = 1

        result_set = sql.con_query("SELECT symbol FROM kraken_coins")
        
        if result_set.rowcount > 0:
            symbol_list = result_set.fetchall()
            total       = len(symbol_list)
            
            for _tuple in symbol_list:
                symbol = _tuple[0]
                G.log.print_and_log(f"{iteration} of {total}: {symbol}")
                
                if symbol not in StableCoins.STABLE_COINS_LIST:
                    if self.is_buy_long(symbol + StableCoins.USD):
                        buy_set.add(symbol)
                iteration+=1
        return buy_set        

    def get_strong_buy_set(self) -> set:
        """
        For every coin on the kraken exchange, 
        get the analysis to see which one is a buy according to the time intervals.
        
        """
        sql       = SQL()
        buy_set   = set()
        iteration = 1

        result_set = sql.con_query("SELECT symbol FROM kraken_coins")
        
        if result_set.rowcount > 0:
            symbol_list = result_set.fetchall()
            total       = len(symbol_list)
            
            for _tuple in symbol_list:
                symbol = _tuple[0]
                G.log.print_and_log(f"{iteration} of {total}: {symbol}")
                
                if symbol not in StableCoins.STABLE_COINS_LIST:
                    if self.is_strong_buy(symbol + StableCoins.USD):
                        buy_set.add(symbol)
                iteration+=1
        return buy_set   
