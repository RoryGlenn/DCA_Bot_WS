
from pprint import pprint
from pprint import PrettyPrinter

from bot_features.database.mongo_database import MongoDatabase

from bot_features.low_level.kraken_bot_base import KrakenBotBase
from bot_features.low_level.kraken_enums import *

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

    def buy(self, symbol: str, s_symbol_pair: str):
        max_active_safety_orders     = self.config.DCA_DATA[symbol][ConfigKeys.DCA_SAFETY_ORDERS_ACTIVE_MAX]
        number_of_open_safety_orders = self.mdb.get_number_open_safety_orders(s_symbol_pair)
        iterations                   = max_active_safety_orders - number_of_open_safety_orders
    
        unplaced_safety_orders = self.mdb.get_unplaced_safety_order_data(s_symbol_pair)
        safety_order_numbers   = self.mdb.get_unplaced_safety_order_numbers(s_symbol_pair)

        symbol_pair = s_symbol_pair.split("/")
        symbol_pair = symbol_pair[0] + symbol_pair[1]

        max_volume_prec = self.get_max_volume_precision(symbol_pair)
        max_price_prec  = self.get_max_price_precision(symbol_pair)

        for i in range(iterations):
            safety_order    = unplaced_safety_orders[i]
            quantity_to_buy = self.round_decimals_down(safety_order['quantity'], max_volume_prec)
            required_price  = round(safety_order['required_price'], max_price_prec)

            ### buy ###
            order_result = self.limit_order(Trade.BUY, quantity_to_buy, s_symbol_pair, required_price)
            ###

            if self.has_result(order_result):
                G.log.print_and_log(f"Safety order {safety_order_numbers.pop(0)} placed: {order_result[Dicts.RESULT][Dicts.DESCR][Dicts.ORDER]}", G.print_lock)
            else:
                G.log.print_and_log(f"Could not place safety order {safety_order_numbers.pop(0)} {order_result}", G.print_lock)
        return

    def sell(self):
        return

    def cancel(self):
        return