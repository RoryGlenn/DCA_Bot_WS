import datetime
import sys
import time

from websocket import create_connection

from pprint import pprint
from pprint import PrettyPrinter
from threading import Thread

from bot_features.database.mongo_database import MongoDatabase

from bot_features.socket_handlers.balances_socket_handler import BalancesSocketHandler
from bot_features.socket_handlers.open_orders_socket_handler import OpenOrdersSocketHandler
from bot_features.socket_handlers.own_trades_socket_handler import OwnTradesSocketHandler
from bot_features.socket_handlers.add_order_socket_handler import AddOrderSocketHandler

from bot_features.low_level.kraken_bot_base import KrakenBotBase
from bot_features.low_level.kraken_rest_api import KrakenRestAPI
from bot_features.low_level.kraken_enums import *

from bot_features.tradingview import TradingView

from bot_features.buy import Buy

from bot_features.dca import DCA

from util.colors import Color
from util.config import Config
from util.globals import G


x_list: list = ['XETC', 'XETH', 'XLTC', 'XMLN', 'XREP', 'XXBT', 'XXDG', 'XXLM', 'XXMR', 'XXRP', 'XZEC']
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
        self.api_key = api_key
        self.api_secret = api_secret
        super(KrakenBotBase, self).__init__(self.api_key, self.api_secret)

        self.config: Config        = Config()
        self.tv:     TradingView   = TradingView()
        self.mdb:    MongoDatabase = MongoDatabase()

        # why can't I initialize this variable in kraken_bot_base.py?
        self.asset_pairs_dict = self.get_all_tradable_asset_pairs()[Dicts.RESULT]

        self.socket_handler_open_orders: OpenOrdersSocketHandler = None
        self.socket_handler_own_trades:  OwnTradesSocketHandler  = None
        self.socket_handler_balances:    BalancesSocketHandler   = None
        self.socket_handler_add_order:   AddOrderSocketHandler   = None
        return
    
    def get_buy_dict(self) -> dict:
        """Returns dictionary with (symbol: symbol_pair) relationship"""
        buy_dict = dict()
        
        for symbol in self.config.BUY_COINS:
            alt_name    = self.get_alt_name(symbol)
            symbol_pair = alt_name + StableCoins.USD
            G.log.print_and_log(f"Main thread: checking {symbol_pair}", G.print_lock)
            if self.tv.is_buy(symbol_pair, self.config.TRADINGVIEW_TIME_INTERVALS):
                if symbol in x_list:
                    buy_dict[symbol] = symbol + "/" + StableCoins.ZUSD
                else:
                    buy_dict[symbol] = symbol + "/" + StableCoins.USD
        return buy_dict

    def init_socket_handlers(self, ws_token: str) -> None:
        self.socket_handler_open_orders = OpenOrdersSocketHandler(ws_token)
        self.socket_handler_own_trades  = OwnTradesSocketHandler(ws_token)
        self.socket_handler_balances    = BalancesSocketHandler(ws_token)
        self.socket_handler_add_order   = AddOrderSocketHandler(ws_token)
        return

    def start_socket_handler_threads(self) -> None:
        Thread(target=self.socket_handler_open_orders.ws_thread).start()
        Thread(target=self.socket_handler_own_trades.ws_thread).start()
        Thread(target=self.socket_handler_balances.ws_thread).start()
        Thread(target=self.socket_handler_add_order.ws_thread).start()
        return

    def buy(self, buy_dict: dict, ws_token: str) -> None:
        """Place buy order for each symbol_pair in buy_dict"""
        for symbol, symbol_pair in buy_dict.items():
            if self.mdb.c_open_symbols.count_documents({"symbol_pair": symbol_pair}) == 0:
                """symbol_pair is not in database."""
                order_list        = []
                pair              = symbol_pair.split("/")
                order_min         = self.get_order_min(pair[0] + pair[1])
                market_price      = self.get_bid_price(symbol_pair)

                base_order_size   = self.config.BASE_ORDER_SIZE
                safety_order_size = self.config.SAFETY_ORDER_SIZE

                if self.config.BASE_ORDER_SIZE < order_min:
                    base_order_size = order_min

                if self.config.SAFETY_ORDER_SIZE < order_min:
                    safety_order_size = order_min

                dca = DCA(symbol, symbol_pair, base_order_size, safety_order_size, market_price)
                dca.start()

                if self.config.ALL_OR_NOTHING:
                    total_cost = dca.total_cost_levels[-1]
                    if total_cost > G.available_usd:
                        continue

                order_list.append('{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "price":"%(price)s", "volume":"%(volume)s"}' 
                    % {"feed": "addOrder", "token": ws_token, "pair": "XBT/USD", "type": "buy", "ordertype": "limit", "price": 1, "volume": 1})

                # dca.store_in_db()

                # base order
                # order_list.append('{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "volume":"%(volume)s"}' \
                #     % {"feed": "addOrder", "token": ws_token, "pair": symbol_pair, "type": "buy", "ordertype": "market", "volume": base_order_size})
                
                # # safety orders
                # for i in range(self.config.SAFETY_ORDERS_MAX):
                #     order_list.append('{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "price":"%(price)s", "volume":"%(volume)s"}' \
                #         % {"feed": "addOrder", "token": ws_token, "pair": symbol_pair, "type": "buy", "ordertype": "limit", "price": dca.price_levels[i], "volume": dca.quantities[i]})

                # TO CHECK FOR
                # 1. the user doesn't have the funds available (create the safety order table and place as many orders as possible. Check back when we can place the remaining safety orders)
                # 2. the user does have the funds (place the base order and safety orders all at once)
                # 3. when do we store, in the database? when the order went through or before? (If the base order went through, create a safety order table and try to place the remaining safety orders.)

                # do we try to put in the base order and all safety orders at the same time? (depends on the active max)

                G.add_orders_lock.acquire()
                G.add_orders_queue.append(order_list)
                G.add_orders_lock.release()
            else:
                """symbol_pair is in database."""
            return

    def start_trade_loop(self) -> None:
        try:
            ws_token = self.get_web_sockets_token()["result"]["token"]
        except Exception as e:
            G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
            sys.exit(0)

        self.init_socket_handlers(ws_token)
        self.start_socket_handler_threads()

        while True:
            start_time = time.time()
            buy_dict   = self.get_buy_dict()

            G.log.print_and_log(Color.FG_BRIGHT_BLACK + f"Main thread: checked all coins in {get_elapsed_time(start_time)}" + Color.ENDC, G.print_lock)
            
            buy_list = [symbol_pair for (symbol, symbol_pair) in buy_dict.items()]
            
            G.log.print_and_log(f"Main thread: buy list {PrettyPrinter(indent=1).pformat(buy_list)}", G.print_lock)

            self.buy(buy_dict, ws_token)
            
            self.wait(message=Color.FG_BRIGHT_BLACK   + f"Main thread: waiting till {get_buy_time()} to buy" + Color.ENDC, timeout=60)
        return
