import datetime
import sys
import time
import pymongo

from pprint import pprint
from pprint import PrettyPrinter
from threading import Thread

from socket_handlers.balances_socket_handler import BalancesSocketHandler
from socket_handlers.open_orders_socket_handler import OpenOrdersSocketHandler
from socket_handlers.own_trades_socket_handler import OwnTradesSocketHandler
from socket_handlers.add_order_socket_handler import AddOrderSocketHandler

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

        self.db            = pymongo.MongoClient()[DB.DATABASE_NAME]
        self.collection_os = self.db[DB.COLLECTION_OS]

        # why can't I initialize this variable in kraken_bot_base.py?
        self.asset_pairs_dict   = self.get_all_tradable_asset_pairs()[Dicts.RESULT]
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
        
        # Thread(target=sh_open_orders.ws_thread).start()
        Thread(target=sh_own_trades.ws_thread).start()
        # Thread(target=sh_balances.ws_thread).start()
        
        while True:
            start_time = time.time()
            buy_dict   = self.get_buy_dict()
            buy_list   = [symbol_pair for (symbol, symbol_pair) in buy_dict.items()]

            G.log.print_and_log(f"Main thread: buy list {PrettyPrinter().pformat(buy_list)}", G.lock)
            for symbol, symbol_pair in buy_dict.items():
                if self.collection_os.count_documents({"symbol_pair": symbol_pair}) == 0:

                    ### PLACE BUY ORDER! ###
                    order_min         = self.get_order_min(symbol_pair)
                    base_order_size   = self.BASE_ORDER_SIZE
                    safety_order_size = self.SAFETY_ORDER_SIZE

                    if self.BASE_ORDER_SIZE < order_min:
                        base_order_size = order_min

                    if self.SAFETY_ORDER_SIZE < order_min:
                        safety_order_size = order_min

                    result = self.market_order(Trade.BUY, base_order_size, symbol_pair)
                    
                    if not self.has_result(result):
                        G.log.print_and_log(Color.FG_BRIGHT_BLACK + f"Main thread: Error: {result}" + Color.ENDC, G.lock)
                    break

            # G.log.print_and_log(Color.FG_BRIGHT_BLACK + f"Main thread: checked all coins in {get_elapsed_time(start_time)}" + Color.ENDC, G.lock)
            # self.wait(message=Color.FG_BRIGHT_BLACK   + f"Main thread: waiting till {get_buy_time()} to buy" + Color.ENDC, timeout=60)
            time.sleep(100)
        return
