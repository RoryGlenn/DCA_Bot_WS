import time

from pprint                                 import pprint

from bot_features.database.mongo_database   import MongoDatabase

from bot_features.low_level.kraken_bot_base import KrakenBotBase
from bot_features.low_level.kraken_enums    import *

from util.config                            import g_config
from util.globals                           import G


x_list:   list = ['XETC', 'XETH', 'XLTC', 'XMLN', 'XREP', 'XXBT', 'XXDG', 'XXLM', 'XXMR', 'XXRP', 'XZEC']
reg_list: list = ['ETC', 'ETH', 'LTC', 'MLN', 'REP', 'XBT', 'XDG', 'XLM', 'XMR', 'XRP', 'ZEC']


class SafetyOrder(KrakenBotBase):
    def __init__(self, api_key: str, api_secret: str) -> None:
        super().__init__(api_key, api_secret)
        self.mdb:    MongoDatabase = MongoDatabase()
        return

    def buy(self, symbol: str, s_symbol_pair: str):
        max_active_safety_orders     = g_config.DCA_DATA[symbol][ConfigKeys.DCA_SAFETY_ORDERS_ACTIVE_MAX]
        number_of_open_safety_orders = self.mdb.get_number_of_open_safety_orders(s_symbol_pair)
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
            price           = round(safety_order['price'], max_price_prec)

            ### buy ###
            order_result = self.limit_order(Trade.BUY, quantity_to_buy, s_symbol_pair, price)
            time.sleep(1)
            ###########

            safety_order_num = safety_order_numbers.pop(0)

            if self.has_result(order_result):
                G.log.print_and_log(f"{s_symbol_pair} Safety order {safety_order_num} placed: {order_result[Dicts.RESULT][Dicts.DESCR][Dicts.ORDER]}", G.print_lock)
                
                # store the buy order txid
                buy_order_txid = order_result[Dicts.RESULT][Data.TXID][0]
                self.mdb.store_safety_order_buy_txid(s_symbol_pair, safety_order_num, buy_order_txid)
                self.mdb.update_placed_safety_order(s_symbol_pair, safety_order_num, buy_order_txid)
            else:
                G.log.print_and_log(f"{s_symbol_pair} Could not place safety order {safety_order_num} {order_result}", G.print_lock)
        return

    def sell(self, s_symbol_pair: str, so_num: str) -> None:
        so_data        = self.mdb.get_safety_order_data_by_num(s_symbol_pair, so_num) 
        print(so_data)

        symbol_pair = s_symbol_pair.split("/")
        symbol_pair = symbol_pair[0] + symbol_pair[1]

        max_price_prec  = self.get_max_price_precision(symbol_pair)
        max_volume_prec = self.get_max_volume_precision(symbol_pair)

        price          = round(float(so_data['price']), max_price_prec)
        total_quantity = self.round_decimals_down(float(so_data['total_quantity']), max_volume_prec)
        
        G.log.print_and_log(f"{s_symbol_pair}, price: {price}, total_quantity: {total_quantity}", G.print_lock)
        
        # place the new sell safety order
        order_result = self.limit_order(Trade.SELL, total_quantity, s_symbol_pair, price)

        if self.has_result(order_result):
            G.log.print_and_log(f"{s_symbol_pair} safety order sell {so_num} placed {order_result[Dicts.RESULT][Dicts.DESCR][Dicts.ORDER]}", G.print_lock)
        else:
            G.log.print_and_log(f"{s_symbol_pair} sell order did not go through! {order_result}", G.print_lock)        
        return

    def cancel_sell(self, s_symbol_pair: str, so_num: int) -> None:
        # cancel the sell limit safety order whose so_num is: filled_so_nums[-1] - 1
        txid_to_cancel = self.mdb.get_safety_order_sell_txid(s_symbol_pair, so_num)
        
        G.log.print_and_log(f"{s_symbol_pair} txid to cancel: {txid_to_cancel}", G.print_lock)
        
        order_result = self.cancel_order(txid_to_cancel)

        G.log.print_and_log(f"{s_symbol_pair} cancel order result: {order_result}", G.print_lock)
        
        self.mdb.cancel_sell_order(s_symbol_pair, txid_to_cancel)
        return