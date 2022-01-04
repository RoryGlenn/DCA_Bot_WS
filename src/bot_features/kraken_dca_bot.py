import datetime
import time

from pprint import pprint
from pprint import PrettyPrinter
from threading import Thread

from bot_features.orders.base_order import BaseOrder
from bot_features.orders.safety_order import SafetyOrder

from bot_features.database.mongo_database import MongoDatabase
from bot_features.low_level.kraken_rest_api import KrakenRestAPI

from bot_features.socket_handlers.balances_socket_handler import BalancesSocketHandler
from bot_features.socket_handlers.open_orders_socket_handler import OpenOrdersSocketHandler
from bot_features.socket_handlers.own_trades_socket_handler import OwnTradesSocketHandler

from bot_features.low_level.kraken_bot_base import KrakenBotBase
from bot_features.low_level.kraken_enums import *

from bot_features.tradingview import TradingView

from bot_features.dca import DCA

from util.colors  import Color
from util.globals import G

from util.config import g_config


x_list:   list = ['XETC', 'XETH', 'XLTC', 'XMLN', 'XREP', 'XXBT', 'XXDG', 'XXLM', 'XXMR', 'XXRP', 'XZEC']
reg_list: list = ['ETC', 'ETH', 'LTC', 'MLN', 'REP', 'XBT', 'XDG', 'XLM', 'XMR', 'XRP', 'ZEC']


def get_elapsed_time(start_time: float) -> str:
    end_time     = time.time()
    elapsed_time = round(end_time - start_time)
    minutes      = elapsed_time // 60
    seconds      = elapsed_time % 60
    return f"{minutes} minutes {seconds} seconds"

def get_buy_time() -> str:
    """Returns the next time to buy as specified in the config file."""
    return ( datetime.timedelta(minutes=Buy_.TIME_MINUTES) + datetime.datetime.now() ).strftime("%H:%M:%S")



class KrakenDCABot(KrakenBotBase):
    def __init__(self, api_key, api_secret) -> None:
        super().__init__(api_key, api_secret)
        self.api_key:       str           = api_key
        self.api_secret:    str           = api_secret
        self.rest_api:      KrakenRestAPI = KrakenRestAPI(api_key, api_secret)
        self.base_order:    BaseOrder     = BaseOrder(api_key, api_secret)
        self.safety_orders: SafetyOrder   = SafetyOrder(api_key, api_secret)
        self.tv:            TradingView   = TradingView()
        self.mdb:           MongoDatabase = MongoDatabase()
        return

    def is_ok(self, order_result: dict):
        if isinstance(order_result, dict):
            if 'status' in order_result:
                return order_result['status'] == 'ok'
        return False
    
    def get_buy_dict(self) -> dict:
        """Returns dictionary with (symbol: symbol_pair) relationship"""
        buy_dict = dict()
        
        for symbol in g_config.DCA_DATA:
            alt_name    = self.get_alt_name('X' + symbol) if symbol in reg_list else self.get_alt_name(symbol)
            symbol_pair = alt_name + StableCoins.USD

            G.log.print_and_log(f"Main thread: checking {symbol_pair}", G.print_lock)

            if self.tv.is_buy(symbol_pair, g_config.DCA_DATA[symbol]['dca_time_intervals']):
                if symbol in x_list:
                    buy_dict[symbol] = symbol + "/" + StableCoins.ZUSD
                else:
                    buy_dict[symbol] = symbol + "/" + StableCoins.USD
        return buy_dict

    def init_socket_handlers(self, ws_token: str) -> None:
        G.socket_handler_open_orders = OpenOrdersSocketHandler(ws_token)
        G.socket_handler_own_trades  = OwnTradesSocketHandler(ws_token)
        G.socket_handler_balances    = BalancesSocketHandler(ws_token)
        return

    def start_socket_handler_threads(self) -> None:
        Thread(target=G.socket_handler_open_orders.ws_thread).start()
        Thread(target=G.socket_handler_own_trades.ws_thread).start()
        Thread(target=G.socket_handler_balances.ws_thread).start()
        return

    # def cancel_orders(self, symbol_pair: str) -> None:
    #     open_orders = self.get_open_orders()['result']['open']
    #     for txid, data in open_orders.items():
    #         if data['descr']['pair'] == symbol_pair:
    #             self.cancel_order(txid)        
    #     return

    def start_trade_loop(self) -> None:
        ws_token = self.get_web_sockets_token()["result"]["token"]

        self.init_socket_handlers(ws_token)
        self.start_socket_handler_threads()

        ##################################
        # self.mdb.c_safety_orders.drop()
        # self.mdb.c_open_symbols.drop()
        # self.mdb.c_own_trades.drop()
        ##################################

        time.sleep(5)

        while True:
            # if we cancel an order, which if block will execute inside of open_orders_socket_handler.py?

            # print("1: G.available_usd", G.available_usd)
            # time.sleep(45)
            
            # order_result = self.limit_order(Trade.BUY, 10000, "SC/USD", 0.0001)
            # time.sleep(1)
            # txid = order_result['result']['txid'][0]

            # # cancel the order manually right here!!!
            # time.sleep(1)
            # self.cancel_order(txid)
            # time.sleep(1)
            # print("2: G.available_usd", G.available_usd)
            
            start_time = time.time()
            buy_dict = self.get_buy_dict()

            G.log.print_and_log(Color.FG_BRIGHT_BLACK + f"Main thread: checked all coins in {get_elapsed_time(start_time)}" + Color.ENDC, G.print_lock)
            G.log.print_and_log(f"Main thread: buy list {PrettyPrinter(indent=1).pformat([symbol_pair for (_, symbol_pair) in buy_dict.items()])}", G.print_lock)

            # place safety orders for previous trades before starting a new trade
            # for elem in self.mdb.c_safety_orders.find():
            #     for symbol, symbol_pair in elem.items():
            #         self.place_safety_orders(ws_token, symbol, symbol_pair)

            for symbol, symbol_pair in buy_dict.items():
                if not self.mdb.in_safety_orders(symbol_pair):
                    base_order_result = self.base_order.buy(symbol, symbol_pair)
                    
                    if self.is_ok(base_order_result):
                        base_order_result = self.base_order.sell(symbol_pair)
                        self.safety_orders.buy(symbol, symbol_pair)
            
            self.wait(message=Color.FG_BRIGHT_BLACK   + f"Main thread: waiting till {get_buy_time()} to buy" + Color.ENDC, timeout=60)
        return
