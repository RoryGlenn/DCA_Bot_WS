import os
import time
import datetime
import sys

from threading import Thread
from pprint import pprint

from bot_features.buy import Buy
from bot_features.sell import Sell
from bot_features.kraken_bot_base import KrakenBotBase
from bot_features.kraken_enums import *
from bot_features.tradingview import TradingView

from socket_handlers.open_orders_socket_handler import OpenOrdersSocketHandler
from socket_handlers.own_trades_socket_handler import OwnTradesSocketHandler
from socket_handlers.balances_socket_handler import BalancesSocketHandler
from util.colors import Color

from util.config_parser import Config
from util.globals import G


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
        self.start_time: float = 0.0
        return
    
    def start_trade_loop(self) -> None:
        try:
            ws_token = self.get_web_sockets_token()["result"]["token"]
        except Exception as e:
            print(e)
            sys.exit(0)

        sh_open_orders = OpenOrdersSocketHandler(ws_token)
        sh_own_trades  = OwnTradesSocketHandler(ws_token)
        sh_balances    = BalancesSocketHandler(ws_token)
        
        Thread(target=sh_open_orders.ws_thread).start()
        Thread(target=sh_own_trades.ws_thread).start()
        Thread(target=sh_balances.ws_thread).start()
        start_time = 0
        
        while True:
            start_time = time.time()
            
            if self.has_finished_first_iteration:
                buy_list = []
                
                for symbol in self.BUY_COINS:
                    alt_name    = self.get_alt_name(symbol) 
                    symbol_pair = alt_name + StableCoins.USD
                    
                    G.log.print_and_log(f"Main thread: checking {symbol}", G.lock)
                    
                    if self.is_buy(symbol_pair, self.TRADINGVIEW_TIME_INTERVALS):
                        buy_list.append(symbol_pair)
                   
                G.log.print_and_log(f"Main thread: buy list {buy_list}", G.lock)
            
            G.log.print_and_log(Color.FG_BRIGHT_BLACK + f"Main thread: checked all coins in {get_elapsed_time(start_time)}" + Color.ENDC, G.lock)
            self.wait(message=Color.FG_BRIGHT_BLACK + f"Main thread: waiting till {get_buy_time()} to buy" + Color.ENDC, timeout=60)
        return