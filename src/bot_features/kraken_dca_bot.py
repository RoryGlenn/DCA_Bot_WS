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
from util.config  import Config
from util.globals import G


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

        self.api_key:    str           = api_key
        self.api_secret: str           = api_secret

        self.rest_api:   KrakenRestAPI = KrakenRestAPI(api_key, api_secret)
        self.base_order: BaseOrder     = BaseOrder(api_key, api_secret)
        self.safety_order: SafetyOrder = SafetyOrder(api_key, api_secret)
        self.config:     Config        = Config()
        self.tv:         TradingView   = TradingView()
        self.mdb:        MongoDatabase = MongoDatabase()
        self.dca:        DCA           = None
        return

    def is_ok(self, order_result: dict):
        if isinstance(order_result, dict):
            if 'status' in order_result:
                return order_result['status'] == 'ok'
        return False
    
    def get_buy_dict(self) -> dict:
        """Returns dictionary with (symbol: symbol_pair) relationship"""
        buy_dict = dict()
        
        for symbol in self.config.DCA_DATA:
            alt_name    = self.get_alt_name('X' + symbol) if symbol in reg_list else self.get_alt_name(symbol)
            symbol_pair = alt_name + StableCoins.USD

            G.log.print_and_log(f"Main thread: checking {symbol_pair}", G.print_lock)

            if self.tv.is_buy(symbol_pair, self.config.DCA_DATA[symbol]['dca_time_intervals']):
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
    
    def place_base_order(self, ws_token: str, symbol: str, symbol_pair: str) -> dict:
        """Place buy order for symbol_pair."""
        pair         = symbol_pair.split("/")
        order_min    = self.get_order_min('X' + pair[0] + StableCoins.ZUSD) if pair[0] in reg_list else self.get_order_min(pair[0] + pair[1])
        market_price = self.get_bid_price(symbol_pair)

        base_order_size   = self.config.DCA_DATA[symbol][ConfigKeys.DCA_BASE_ORDER_SIZE] 
        safety_order_size = self.config.DCA_DATA[symbol][ConfigKeys.DCA_SAFETY_ORDER_SIZE]

        if base_order_size < order_min:
            G.log.print_and_log(f"{symbol} Base order size must be at least {order_min}", G.print_lock)
            return {'status': f'Base order size must be at least {order_min}'}
        if safety_order_size < order_min:
            G.log.print_and_log(f"{symbol} Safety order size must be at least {order_min}", G.print_lock)
            return {'status': f'Safety order size must be at least {order_min}'}

        dca = DCA(symbol, symbol_pair, base_order_size, safety_order_size, market_price)
        dca.start()

        if self.config.DCA_DATA[symbol][ConfigKeys.DCA_ALL_OR_NOTHING]:
            total_cost = dca.total_cost_levels[-1]
            if total_cost > G.available_usd:
                return {'status': 'DCA_ALL_OR_NOTHING'}

        # for now, all base order buys must be market
        self.socket_handler_base_order.ws_buy_sync(ws_token, symbol_pair, "market", base_order_size)

        if self.socket_handler_base_order.is_buy_order_ok():
            G.log.print_and_log(f"{symbol_pair} Base order placed {self.socket_handler_base_order.buy_order_result}", G.print_lock)
            
            descr       = self.socket_handler_base_order.buy_order_result['descr'].split(' ')
            # quantity    = float(descr[1])
            # order_type  = descr[4]
            order_txid  = self.socket_handler_base_order.buy_order_result['txid']
            
            entry_price = self.socket_handler_own_trades.get_entry_price(order_txid)
            self.dca    = DCA(symbol, symbol_pair, base_order_size, safety_order_size, float(entry_price))
            self.dca.start()
            self.dca.store_in_db()
        else:
            print(f"Error: order did not go through! {self.socket_handler_base_order.buy_order_result}")
        return self.socket_handler_base_order.buy_order_result

    def place_base_sell_order(self, ws_token: str, pair: str) -> None:
        if self.socket_handler_base_order.is_buy_order_ok():
            # Round self.dca.base_target_price
            _symbol_pair    = pair.split("/")
            _symbol_pair    = _symbol_pair[0] + _symbol_pair[1]
            max_price_prec  = self.get_max_price_precision(_symbol_pair)
            target_price    = self.round_decimals_down(self.dca.base_target_price, max_price_prec)

            # place the sell order
            limit_order_result = self.rest_api.limit_order(Trade.SELL, self.dca.base_order_size, _symbol_pair, target_price)

            if Dicts.RESULT in limit_order_result.keys():
                G.log.print_and_log(f"{pair} Sell order placed {limit_order_result[Dicts.RESULT][Dicts.DESCR][Dicts.ORDER]}", G.print_lock)
            else:
                G.log.print_and_log(f"{pair} Sell order NOT placed {limit_order_result}", G.print_lock)
        return

    def place_safety_orders(self, ws_token: str, base_order_result: dict, symbol: str, symbol_pair: str) -> None:
        # if number_of_open_safety_order >= self.config.DCA_DATA[symbol][ConfigKeys.DCA_SAFETY_ORDERS_ACTIVE_MAX]:
        #     return

        if base_order_result['status'] == 'ok':
            for i in range(self.config.DCA_DATA[symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
                self.socket_handler_safety_order.ws.send('{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "price":"%(price)s", "volume":"%(volume)s"}'
                    % {"feed": "addOrder", "token": ws_token, "pair": symbol_pair, "type": "buy", "ordertype": "limit", "price": i, "volume": i})

                while len(self.socket_handler_safety_order.order_result) == 0:
                    time.sleep(0.05)

                has_safety_order = False
                
                if self.socket_handler_safety_order.order_result['status'] == 'ok':
                    G.log.print_and_log(f"{symbol_pair} Safety order placed {self.socket_handler_safety_order.order_result}", G.print_lock)

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
                else:
                    G.log.print_and_log(f"{symbol_pair} Safety order not placed {self.socket_handler_safety_order.order_result}", G.print_lock)
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
        # self.mdb.c_safety_orders.drop()
        # self.mdb.c_open_symbols.drop()
        # self.mdb.c_own_trades.drop()
        # self.cancel_orders("XBTUSD")
        # self.cancel_orders("SCUSD")
        ##################################

        while True:
            max_active_safety_orders     = self.config.DCA_DATA["SC"][ConfigKeys.DCA_SAFETY_ORDERS_ACTIVE_MAX]
            number_of_open_safety_orders = self.mdb.get_number_open_safety_orders("SC/USD")

            start_time = time.time()
            buy_dict   = self.get_buy_dict()

            G.log.print_and_log(Color.FG_BRIGHT_BLACK + f"Main thread: checked all coins in {get_elapsed_time(start_time)}" + Color.ENDC, G.print_lock)
            G.log.print_and_log(f"Main thread: buy list {PrettyPrinter(indent=1).pformat([symbol_pair for (symbol, symbol_pair) in buy_dict.items()])}", G.print_lock)

            # place safety orders for previous trades before starting a new trade
            # for elem in self.mdb.c_safety_orders.find():
            #     for symbol, symbol_pair in elem.items():
            #         self.place_safety_orders(ws_token, symbol, symbol_pair)

            buy_dict = {'SC': 'SC/USD'} # for testing only

            for symbol, symbol_pair in buy_dict.items():
                if not self.mdb.in_safety_orders(symbol_pair):
                    base_order_result = self.base_order.buy(symbol, symbol_pair)
                    
                    if self.is_ok(base_order_result):
                        base_order_result = self.base_order.sell(symbol_pair)
                        self.safety_order.place_orders(symbol, symbol_pair)
                        # self.place_safety_orders(ws_token, base_order_result, symbol, symbol_pair)
            
            self.wait(message=Color.FG_BRIGHT_BLACK   + f"Main thread: waiting till {get_buy_time()} to buy" + Color.ENDC, timeout=60)
        return
