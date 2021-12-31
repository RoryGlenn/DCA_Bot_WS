import datetime
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


x_list:   list = ['XETC', 'XETH', 'XLTC', 'XMLN', 'XREP', 'XXBT', 'XXDG', 'XXLM', 'XXMR', 'XXRP', 'XZEC']
reg_list: list = ['ETC', 'ETH', 'LTC', 'MLN', 'REP', 'XBT', 'XDG', 'XLM', 'XMR', 'XRP', 'ZEC']


class BaseOrder(KrakenBotBase):
    def __init__(self, api_key: str, api_secret: str) -> None:
        super(KrakenBotBase, self).__init__(api_key, api_secret)
        self.config:                    Config                 = Config()
        self.socket_handler_base_order: BaseOrderSocketHandler = None
        return

    def is_ok(self) -> bool:
        while len(self.socket_handler_base_order.order_result) == 0:
            time.sleep(0.05)
        return bool(self.socket_handler_base_order.order_result['status'] == 'ok')

    def buy(self, ws_token: str, symbol: str, symbol_pair: str):
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

        base_order = '{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "volume":"%(volume)s"}' \
            % {"feed": "addOrder", "token": ws_token, "pair": symbol_pair, "type": "buy", "ordertype": "market", "volume": base_order_size}

        self.socket_handler_base_order.ws.send(base_order)

        if self.is_ok():
            G.log.print_and_log(f"{symbol_pair} Base order placed {self.socket_handler_base_order.order_result}", G.print_lock)
            
            descr       = self.socket_handler_base_order.order_result['descr'].split(' ')
            # quantity    = float(descr[1])
            # order_type  = descr[4]
            entry_price = float(descr[5]) # {'descr': 'buy 280.00000000 SCUSD @ market', 'event': 'addOrderStatus', 'status': 'ok', 'txid': 'OY2E4E-EJCGS-FDBOWZ'}
            txid        = self.socket_handler_base_order.order_result['txid']
            
            self.dca = DCA(symbol, symbol_pair, base_order_size, safety_order_size, entry_price)
            self.dca.start()
            self.dca.store_in_db()
        else:
            print(f"Error: order did not go through! {self.socket_handler_base_order.order_result}")
        return self.socket_handler_base_order.order_result

    def sell(self):
        return

    def cancel_sell(self):
        return