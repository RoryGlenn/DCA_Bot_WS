from pprint import pprint

from bot_features.database.mongo_database import MongoDatabase

from bot_features.socket_handlers.base_order_socket_handler import BaseOrderSocketHandler

from bot_features.low_level.kraken_bot_base import KrakenBotBase
from bot_features.low_level.kraken_enums import *

from bot_features.dca import DCA

from util.config  import Config
from util.globals import G


x_list:   list = ['XETC', 'XETH', 'XLTC', 'XMLN', 'XREP', 'XXBT', 'XXDG', 'XXLM', 'XXMR', 'XXRP', 'XZEC']
reg_list: list = ['ETC', 'ETH', 'LTC', 'MLN', 'REP', 'XBT', 'XDG', 'XLM', 'XMR', 'XRP', 'ZEC']


class BaseOrder(KrakenBotBase):
    def __init__(self, api_key: str, api_secret: str) -> None:
        super().__init__(api_key, api_secret)
        self.config:                    Config                 = Config()
        self.socket_handler_base_order: BaseOrderSocketHandler = None
        self.mdb:                       MongoDatabase          = MongoDatabase()
               
        return

    def get_entry_price(self, order_result: dict) -> str:
        order_txid = order_result[Dicts.RESULT][Data.TXID][0]

        for _, trade_info in G.socket_handler_own_trades.trades.items():
            if trade_info[Data.ORDER_TXID] == order_txid:
                return float(trade_info['price'])
        raise Exception("No base order price was found!")

    def buy(self, symbol: str, symbol_pair: str):
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

        if self.config.DCA_DATA[symbol][ConfigKeys.DCA_ALL_OR_NOTHING]:
            dca = DCA(symbol, symbol_pair, base_order_size, safety_order_size, market_price)
            dca.start()
            
            total_cost = dca.total_cost_levels[-1]
            if total_cost > G.available_usd:
                return {'status': 'DCA_ALL_OR_NOTHING'}

        order_result = self.market_order(Trade.BUY, base_order_size, pair[0]+pair[1])

        if self.has_result(order_result):
            G.log.print_and_log(f"{symbol_pair} Base order placed {order_result[Dicts.RESULT][Dicts.DESCR][Dicts.ORDER]}", G.print_lock)
            
            entry_price = self.get_entry_price(order_result)
            self.dca    = DCA(symbol, symbol_pair, base_order_size, safety_order_size, entry_price)
            
            self.dca.start()
            self.dca.store_in_db()
        else:
            G.log.print_and_log(f"Error: order did not go through! {order_result}")
            return {'status': f"order did not go through! {order_result}"}
        return {'status': 'ok', 'order_result': order_result}

    def sell(self, symbol_pair: str):
        """place a limit order for the base order."""

        # {'error': [], 'result': {'txid': ['ODKZNJ-REY6H-36ECRM'], 'descr': {'order': 'buy 280.00000000 SCUSD @ market'}}}
        
        print(Trade.SELL, self.dca.base_order_size, symbol_pair, self.dca.base_target_price)

        sell_order_result = self.limit_order(Trade.SELL, self.dca.base_order_size, symbol_pair, self.dca.base_target_price)

        pprint(sell_order_result, sort_dicts=False)

        if self.has_result(sell_order_result):
            # what should we store in the database after we place the sell for our base order???
            for document in self.mdb.c_safety_orders.find({'_id': symbol_pair}):
                for value in document.values():
                    if isinstance(value, dict):
                        for safety_order in value['safety_orders']:
                            for safety_order_no, safety_order_data in safety_order.items():
                                if not has_safety_order:
                                    if safety_order_data['has_placed_sell_order'] == False:
                                        safety_order_data['has_placed_sell_order'] = True
                                        
                                        new_values = {"$set": {symbol_pair: value}}
                                        query      = {'_id': symbol_pair}
                                        self.mdb.c_safety_orders.find_one_and_update(query, new_values)
                                        has_safety_order = True
                                        break
        else:
            G.log.print_and_log(f'could not place limit order sell for {symbol_pair}: {sell_order_result}')
            return {'status': f'could not place limit order sell for {symbol_pair}: {sell_order_result}'}

        return {'status': 'ok'}

    def cancel_sell(self):
        """If a safety order has filled while the base sell order has not filled, cancel the base sell order"""
        return