import datetime
import sys
import time


from pprint import pprint
from pprint import PrettyPrinter
from threading import Thread

from bot_features.database.mongo_database import MongoDatabase

from bot_features.socket_handlers.balances_socket_handler import BalancesSocketHandler
from bot_features.socket_handlers.open_orders_socket_handler import OpenOrdersSocketHandler
from bot_features.socket_handlers.own_trades_socket_handler import OwnTradesSocketHandler
from bot_features.socket_handlers.safety_order_socket_handler import SafetyOrderSocketHandler
from bot_features.socket_handlers.base_order_socket_handler import BaseOrderSocketHandler

from bot_features.low_level.kraken_bot_base import KrakenBotBase
from bot_features.low_level.kraken_enums import *

from bot_features.tradingview import TradingView

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

        self.socket_handler_open_orders:  OpenOrdersSocketHandler  = None
        self.socket_handler_own_trades:   OwnTradesSocketHandler   = None
        self.socket_handler_balances:     BalancesSocketHandler    = None
        self.socket_handler_safety_order: SafetyOrderSocketHandler = None
        self.socket_handler_base_order:   BaseOrderSocketHandler   = None
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
        self.socket_handler_open_orders  = OpenOrdersSocketHandler(ws_token)
        self.socket_handler_own_trades   = OwnTradesSocketHandler(ws_token)
        self.socket_handler_balances     = BalancesSocketHandler(ws_token)
        self.socket_handler_safety_order = SafetyOrderSocketHandler(ws_token)
        self.socket_handler_base_order   = BaseOrderSocketHandler(ws_token)
        return

    def start_socket_handler_threads(self) -> None:
        Thread(target=self.socket_handler_open_orders.ws_thread).start()
        Thread(target=self.socket_handler_own_trades.ws_thread).start()
        Thread(target=self.socket_handler_balances.ws_thread).start()
        Thread(target=self.socket_handler_base_order.ws_thread).start()
        Thread(target=self.socket_handler_safety_order.ws_thread).start()
        return

    # def place_base_order(self, buy_dict: dict, ws_token: str) -> None:
    def place_base_order(self, symbol: str, symbol_pair: str, ws_token: str) -> None:
        """Place buy order for symbol_pair"""
    
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
                return

        base_order = '{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "price":"%(price)s", "volume":"%(volume)s"}' \
            % {"feed": "addOrder", "token": ws_token, "pair": "XBT/USD", "type": "buy", "ordertype": "limit", "price": 1, "volume": 1}

        """
        store in db before base order VS store in db after base order:

        ######################################
        Store in db before base order PRO's:
            1. You will have access to all order info in any thread.
            2. Little work for now
            
        Store in db before base order CON's:
            1. Makes a messier db with information that hasn't been executed yet
            2. If the base order doesn't go through successfully, you will have to remove the information associated with symbol_pair

        ######################################
        Store in db after base order PRO's:
            1. DB is neat containing only the information that has been executed
            
        Store in db after base order CON's:
            1. Don't know how to put the base order information in the db because we lose access to the DCA object we just created.

        """


        # base order
        # order_list.append('{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "volume":"%(volume)s"}' \
        #     % {"feed": "addOrder", "token": ws_token, "pair": symbol_pair, "type": "buy", "ordertype": "market", "volume": base_order_size})
        
        self.socket_handler_base_order.ws.send(base_order)

        if self.socket_handler_base_order.order_result['status'] == 'ok':
            pprint(self.socket_handler_base_order.order_result)
            dca = DCA(symbol, symbol_pair, base_order_size, safety_order_size, market_price)
            dca.start()
            dca.store_in_db()

        time.sleep(100000)
        return


    def place_safety_orders(symbol: str, symbol_pair: str, ws_token: str) -> None:
        # get the number of open safety orders on symbol_pair

        # # safety orders
        # for i in range(self.config.SAFETY_ORDERS_MAX):
        #     order_list.append('{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "price":"%(price)s", "volume":"%(volume)s"}' \
        #         % {"feed": "addOrder", "token": ws_token, "pair": symbol_pair, "type": "buy", "ordertype": "limit", "price": dca.price_levels[i], "volume": dca.quantities[i]})

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

            # place the base_order and safety_orders for each symbol in the buy_dict
            for symbol, symbol_pair in buy_dict.items():
                if self.mdb.c_open_symbols.count_documents({"symbol_pair": symbol_pair}) == 0:
                    self.place_base_order(symbol, symbol_pair, ws_token)
                    self.place_safety_orders(symbol, symbol_pair, ws_token)
            
            self.wait(message=Color.FG_BRIGHT_BLACK   + f"Main thread: waiting till {get_buy_time()} to buy" + Color.ENDC, timeout=60)
        return
