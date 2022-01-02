import datetime
import time


from pprint import pprint
from pprint import PrettyPrinter
from threading import Thread

from bot_features.database.mongo_database import MongoDatabase

from bot_features.socket_handlers.safety_order_socket_handler import SafetyOrderSocketHandler
from bot_features.socket_handlers.base_order_socket_handler import BaseOrderSocketHandler

from bot_features.low_level.kraken_bot_base import KrakenBotBase
from bot_features.low_level.kraken_enums import *

from bot_features.tradingview import TradingView

from bot_features.dca import DCA

from util.config  import Config
from util.globals import G

x_list:   list = ['XETC', 'XETH', 'XLTC', 'XMLN', 'XREP', 'XXBT', 'XXDG', 'XXLM', 'XXMR', 'XXRP', 'XZEC']
reg_list: list = ['ETC', 'ETH', 'LTC', 'MLN', 'REP', 'XBT', 'XDG', 'XLM', 'XMR', 'XRP', 'ZEC']


class SafetyOrder(KrakenBotBase):
    def __init__(self, api_key, api_secret) -> None:
        super().__init__(api_key, api_secret)
        self.config: Config        = Config()
        self.mdb:    MongoDatabase = MongoDatabase()
        return

    def place_orders(self, symbol: str, symbol_pair: str):
        # get the number of open safety order from the db
        max_active_safety_orders     = self.config.DCA_DATA[symbol][ConfigKeys.DCA_SAFETY_ORDERS_ACTIVE_MAX]
        number_of_open_safety_orders = self.mdb.get_number_open_safety_orders(symbol_pair)
        iterations                   = max_active_safety_orders - number_of_open_safety_orders

        for i in range(iterations):
            pass

        return

    def sell(self):
        return

    def cancel(self):
        return