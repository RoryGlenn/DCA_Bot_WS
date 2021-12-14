import datetime
import sys
import time

from pprint import pprint
from pprint import PrettyPrinter
from threading import Thread

from socket_handlers.balances_socket_handler import BalancesSocketHandler
from socket_handlers.open_orders_socket_handler import OpenOrdersSocketHandler
from socket_handlers.own_trades_socket_handler import OwnTradesSocketHandler

from util.colors import Color
from util.config import Config
from util.globals import G

from bot_features.buy import Buy
from bot_features.kraken_bot_base import KrakenBotBase
from bot_features.kraken_enums import *
from bot_features.tradingview import TradingView
from bot_features.dca import DCA


def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"

def get_buy_time() -> str:
    """Returns the next time to buy as specified in the config file."""
    return ( datetime.timedelta(minutes=Buy_.TIME_MINUTES) + datetime.datetime.now() ).strftime("%H:%M:%S")


class KrakenDCABot(Config, KrakenBotBase, TradingView, Buy):
    def __init__(self, api_key, api_secret) -> None:
        super().__init__()
        super(KrakenBotBase, self).__init__(api_key, api_secret)
        return
    
    def get_buy_dict(self) -> dict:
        """Returns dictionary with (symbol: symbol_pair) relationship"""
        buy_dict = dict()
        
        for symbol in self.BUY_COINS:
            alt_name    = self.get_alt_name(symbol) 
            symbol_pair = alt_name + StableCoins.USD
            
            G.log.print_and_log(f"Main thread: checking {symbol_pair}", G.lock)
            
            if self.is_buy(symbol_pair, self.TRADINGVIEW_TIME_INTERVALS):
                buy_dict[symbol] = symbol_pair
        return buy_dict


    def start_trade_loop(self) -> None:
        try:
            ws_token = self.get_web_sockets_token()["result"]["token"]
        except Exception as e:
            G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
            sys.exit(0)

        sh_open_orders = OpenOrdersSocketHandler(ws_token)
        sh_own_trades  = OwnTradesSocketHandler(ws_token)
        sh_balances    = BalancesSocketHandler(ws_token)
        
        Thread(target=sh_open_orders.ws_thread).start()
        Thread(target=sh_own_trades.ws_thread).start()
        Thread(target=sh_balances.ws_thread).start()
        
        while True:
            start_time = time.time()
            buy_dict = self.get_buy_dict()
            buy_list = [symbol_pair for (symbol, symbol_pair) in buy_dict.items()]
            G.log.print_and_log(f"Main thread: buy list {PrettyPrinter().pformat(buy_list)}", G.lock)

            for symbol, symbol_pair in buy_dict.items():
                if symbol_pair not in sh_open_orders.open_symbol_pairs:
                    # BUY
                    print(symbol_pair)
                    base_order_min = self.BASE_ORDER_SIZE
                    safety_order_size = self.SAFETY_ORDER_SIZE

                    # if base_order_min == 0, get the min for that coin instead
                    # if safety_order_size == 0, get the min for that coin instead
                    # dca = DCA(symbol, symbol_pair, base_order_min, base_order_entry_price)

            G.log.print_and_log(Color.FG_BRIGHT_BLACK + f"Main thread: checked all coins in {get_elapsed_time(start_time)}" + Color.ENDC, G.lock)
            self.wait(message=Color.FG_BRIGHT_BLACK   + f"Main thread: waiting till {get_buy_time()} to buy" + Color.ENDC, timeout=60)
        return
