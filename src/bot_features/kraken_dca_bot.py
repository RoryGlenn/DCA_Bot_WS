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

from util.colors  import Color
from util.config  import Config
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
        self.dca:    DCA           = None

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
        
        # for symbol in self.config.BUY_COINS:
        for symbol in self.config.DCA_DATA:
            alt_name    = self.get_alt_name('X' + symbol) if symbol in reg_list else self.get_alt_name(symbol)
            symbol_pair = alt_name + StableCoins.USD

            G.log.print_and_log(f"Main thread: checking {symbol_pair}", G.print_lock)

            if symbol == "XETC":
                pass

            if self.tv.is_buy(symbol_pair, self.config.DCA_DATA[symbol]['dca_time_intervals']):
                if symbol in x_list:
                    buy_dict[symbol] = symbol + "/" + StableCoins.ZUSD
                else:
                    buy_dict[symbol] = symbol + "/" + StableCoins.USD
        return buy_dict

    def init_socket_handlers(self, ws_token: str) -> None:
        self.socket_handler_open_orders  = OpenOrdersSocketHandler(ws_token)
        self.socket_handler_own_trades   = OwnTradesSocketHandler(ws_token)
        self.socket_handler_balances     = BalancesSocketHandler(ws_token)

        self.socket_handler_base_order   = BaseOrderSocketHandler(ws_token)
        self.socket_handler_safety_order = SafetyOrderSocketHandler(ws_token)
        return

    def start_socket_handler_threads(self) -> None:
        Thread(target=self.socket_handler_open_orders.ws_thread).start()
        Thread(target=self.socket_handler_own_trades.ws_thread).start()
        Thread(target=self.socket_handler_balances.ws_thread).start()
        Thread(target=self.socket_handler_base_order.ws_thread).start()
        Thread(target=self.socket_handler_safety_order.ws_thread).start()
        return
    
    def get_number_of_open_buy_orders(self):
        return

    # def place_base_order(self, buy_dict: dict, ws_token: str) -> None:
    def place_base_order(self, symbol: str, symbol_pair: str, ws_token: str) -> None:
        """Place buy order for symbol_pair"""
    
        pair              = symbol_pair.split("/")
        order_min         = self.get_order_min(pair[0] + pair[1])
        market_price      = self.get_bid_price(symbol_pair)

        base_order_size   = self.config.DCA_DATA[symbol]['dca_base_order_size']
        safety_order_size = self.config.DCA_DATA[symbol]['dca_safety_order_size']

        if self.config.DCA_DATA[symbol]['dca_base_order_size'] < order_min:
            # raise Exception(f"Base order size must be at least {order_min}")
            base_order_size = order_min
        if self.config.DCA_DATA[symbol]['dca_safety_order_size'] < order_min:
            # raise Exception(f"Safety order size must be at least {order_min}")
            safety_order_size = order_min
        
        dca = DCA(symbol, symbol_pair, base_order_size, safety_order_size, market_price)
        dca.start()

        if self.config.DCA_DATA[symbol]['dca_all_or_nothing']:
            total_cost = dca.total_cost_levels[-1]
            if total_cost > G.available_usd:
                return

        base_order = '{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "price":"%(price)s", "volume":"%(volume)s"}' \
            % {"feed": "addOrder", "token": ws_token, "pair": "XBT/USD", "type": "buy", "ordertype": "limit", "price": 1, "volume": 1}

        self.socket_handler_base_order.ws.send(base_order)
        
        # wait until the variable has been assigned a value
        while len(self.socket_handler_base_order.order_result) == 0:
            time.sleep(0.05)

        if self.socket_handler_base_order.order_result['status'] == 'ok':
            descr       = self.socket_handler_base_order.order_result['descr'].split(' ')
            quantity    = float(descr[1])
            order_type  = descr[4]
            entry_price = float(descr[5])
            txid        = self.socket_handler_base_order.order_result['txid']
            
            self.dca = DCA(symbol, symbol_pair, base_order_size, safety_order_size, entry_price)
            self.dca.start()
            self.dca.store_in_db()
        else:
            print(f"Error: order did not go through! {self.socket_handler_base_order.order_result}")
        return

    def place_safety_orders(self, symbol: str, symbol_pair: str, ws_token: str) -> None:
        # get the number of open safety orders on symbol_pair
        for i in range(self.config.DCA_DATA[symbol]['dca_safety_orders_max']):
            self.socket_handler_safety_order.ws.send('{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "price":"%(price)s", "volume":"%(volume)s"}'
                % {"feed": "addOrder", "token": ws_token, "pair": "XBT/USD", "type": "buy", "ordertype": "limit", "price": i, "volume": i})

            while len(self.socket_handler_safety_order.order_result) == 0:
                time.sleep(0.05)

            has_safety_order = False
            
            if self.socket_handler_safety_order.order_result['status'] == 'ok':
                for document in self.mdb.c_safety_orders.find({'_id': symbol_pair}):
                    for value in document.values():
                        if isinstance(value, dict):
                            for safety_order in value['safety_orders']:
                                for safety_order_no, safety_order_data in safety_order.items():
                                    if not has_safety_order:
                                        if safety_order_data['has_placed_order'] == False:
                                            safety_order_data['has_placed_order'] = True
                                            
                                            new_values = {"$set": {symbol_pair: value}}
                                            query      = {'_id': symbol_pair}
                                            self.mdb.c_safety_orders.find_one_and_update(query, new_values)
                                            has_safety_order = True
                                            break
        return


    def cancel_orders(self, symbol_pair: str) -> None:
        open_orders = self.get_open_orders()['result']['open']
        for txid, data in open_orders.items():
            if data['descr']['pair'] == symbol_pair:
                self.cancel_order(txid)        
        return

    def start_trade_loop(self) -> None:
        ws_token = self.get_web_sockets_token()["result"]["token"]

        self.init_socket_handlers(ws_token)
        self.start_socket_handler_threads()

        ##################################
        self.mdb.c_safety_orders.drop()
        self.mdb.c_open_symbols.drop()
        self.mdb.c_own_trades.drop()
        self.cancel_orders("XBTUSD")
        ##################################

        while True:
            start_time = time.time()
            buy_dict   = self.get_buy_dict()

            G.log.print_and_log(Color.FG_BRIGHT_BLACK + f"Main thread: checked all coins in {get_elapsed_time(start_time)}" + Color.ENDC, G.print_lock)
            G.log.print_and_log(f"Main thread: buy list {PrettyPrinter(indent=1).pformat([symbol_pair for (symbol, symbol_pair) in buy_dict.items()])}", G.print_lock)


            # place safety orders first before starting a new trade
            # self.place_safety_orders(symbol, symbol_pair, ws_token)

            # place the base_order and safety_orders for each symbol in the buy_dict
            for symbol, symbol_pair in buy_dict.items():
                if self.mdb.in_safety_orders(symbol_pair):
                    self.place_base_order(symbol, symbol_pair, ws_token)
                self.place_safety_orders(symbol, symbol_pair, ws_token)
            
            self.wait(message=Color.FG_BRIGHT_BLACK   + f"Main thread: waiting till {get_buy_time()} to buy" + Color.ENDC, timeout=60)
        return
