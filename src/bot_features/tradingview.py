"""tradingview.py - pulls data from tradingview.com to see which coins we should buy."""

from pprint         import pprint
from tradingview_ta import TA_Handler

from bot_features.low_level.kraken_enums import *
from util.globals              import G
# from bot_features.my_sql       import SQL


class TradingView:
    def __get_recommendation(self, symbol_pair: str, interval: str) -> list:
        """Get a recommendation (buy or sell) for the symbol."""
        try:
            symbol_data = TA_Handler(
                symbol=symbol_pair,
                screener=TVData.SCREENER,
                exchange=TVData.EXCHANGE,
                interval=interval,
            )

            analysis = symbol_data.get_analysis()

            if symbol_data is not None and analysis is not None:
                return analysis.summary[TVData.RECOMMENDATION]
        except Exception as e:
            G.log.print_and_log(
                e=e,
                error_type=type(e).__name__,
                filename=__file__,
                tb_lineno=e.__traceback__.tb_lineno,
            )
        return []

    def is_buy(self, symbol_pair: str, tradingview_time_intervals: set):
        """Get recommendations for all intervals in TVData.
        Buy the coin if all intervals indicate a BUY or STRONG_BUY."""

        # for interval in TimeIntervals.USER_INTERVALS:
        for interval in tradingview_time_intervals:
            rec = self.__get_recommendation(symbol_pair, interval)
            if rec != TVData.BUY and rec != TVData.STRONG_BUY:
                return False
        return True

    def get_buy_set(self) -> set:
        """
        For every coin on the kraken exchange,
        get the analysis to see which one is a buy according to the time intervals.

        """

        sql = SQL()
        buy_set = set()
        iteration = 1

        result_set = sql.con_query("SELECT symbol FROM kraken_coins")

        if result_set.rowcount > 0:
            symbol_list = result_set.fetchall()
            total = len(symbol_list)

            for _tuple in symbol_list:
                symbol = _tuple[0]
                G.log.print_and_log(f"{iteration} of {total}: {symbol}")

                if symbol not in StableCoins.STABLE_COINS_LIST:
                    if self.is_buy(symbol + StableCoins.USD):
                        buy_set.add(symbol)
                iteration += 1
        return buy_set
