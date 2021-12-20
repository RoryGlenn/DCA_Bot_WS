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
from bot_features.low_level.kraken_enums import *
from bot_features.tradingview import TradingView

from bot_features.buy import Buy
from bot_features.dca import DCA


from util.colors import Color
from util.config import Config
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


class KrakenDCABot(KrakenBotBase):
    def __init__(self, api_key, api_secret) -> None:
        super(KrakenBotBase, self).__init__(api_key, api_secret)

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
            G.log.print_and_log(f"Main thread: checking {symbol_pair}", G.lock)
            if self.tv.is_buy(symbol_pair, self.config.TRADINGVIEW_TIME_INTERVALS):
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

            G.log.print_and_log(Color.FG_BRIGHT_BLACK + f"Main thread: checked all coins in {get_elapsed_time(start_time)}" + Color.ENDC, G.lock)
            
            buy_list = [symbol_pair for (symbol, symbol_pair) in buy_dict.items()]
            
            G.log.print_and_log(f"Main thread: buy list {PrettyPrinter().pformat(buy_list)}", G.lock)
            
            ws_add_order = create_connection("wss://ws-auth.kraken.com/") 
            print(ws_add_order.recv()) # {"connectionID":11231412236839682046,"event":"systemStatus","status":"online","version":"1.8.8"}

            for symbol, symbol_pair in buy_dict.items():
                # if self.collection_os.count_documents({"symbol_pair": symbol_pair}) == 0:
                if self.mdb.c_open_symbols.count_documents({"symbol_pair": symbol_pair}) == 0:

                    ### PLACE BUY ORDER! ###
                    pair              = symbol_pair.split("/")
                    order_min         = self.get_order_min(pair[0]+pair[1])
                    base_order_size   = self.config.BASE_ORDER_SIZE
                    safety_order_size = self.config.SAFETY_ORDER_SIZE

                    if self.config.BASE_ORDER_SIZE < order_min:
                        base_order_size = order_min

                    if self.config.SAFETY_ORDER_SIZE < order_min:
                        safety_order_size = order_min

                    # sh_add_order.ws_send(symbol_pair="XBT/USD", type=Trade.BUY, order_type="market", quantity=10000000000000000)

                    # An initial connection should be made to the authenticated WebSocket URL wss://ws-auth.kraken.com/ ,
                    # which can then be kept open indefinitely while orders are placed and cancelled.
                    # A single WebSocket connection is designed to support multiple requests,
                    # so it is not necessary (or recommended) to connect/disconnect for each call to the trading endpoints.

                    # Success
                    # {"descr":"buy 0.00200000 XBTUSD @ limit 9857.0 with 5:1 leverage","event":"addOrderStatus","status":"ok","txid":"OPOUJF-BWKCL-FG5DQL"}
                    
                    # Error
                    # {"errorMessage":"EOrder:Order minimum not met","event":"addOrderStatus","status":"error"}

                    market_price = self.get_bid_price(symbol_pair)

                    dca = DCA(symbol, symbol_pair, self.config.BASE_ORDER_SIZE, self.config.SAFETY_ORDER_SIZE, market_price)
                    dca.start()
                    pprint(dca.total_cost_levels)

                    try:
                        api_data = '{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "volume":"%(volume)s"}' \
                            % {"feed": "addOrder", "token": ws_token, "pair": symbol_pair, "type": "buy", "ordertype": "market", "volume": base_order_size}

                        print(api_data)
                        ws_add_order.send(api_data)
                        print(ws_add_order.recv())
                    except Exception as e:
                        print(e)

            ws_add_order.close()
            self.wait(message=Color.FG_BRIGHT_BLACK   + f"Main thread: waiting till {get_buy_time()} to buy" + Color.ENDC, timeout=60)
        return
