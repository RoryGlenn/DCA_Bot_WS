import time

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
        self.config: Config        = Config()
        self.mdb:    MongoDatabase = MongoDatabase()
        return

    def get_entry_price(self, order_result: dict) -> str:
        order_txid = order_result[Dicts.RESULT][Data.TXID][0]

        for _, trade_info in G.socket_handler_own_trades.trades.items():
            if trade_info[Data.ORDER_TXID] == order_txid:
                return float(trade_info['price'])
        raise Exception("No base order price was found!")

    def all_or_nothing(self, symbol: str, symbol_pair: str, base_order_size: float, safety_order_size: float, market_price: float) -> bool:
        if self.config.DCA_DATA[symbol][ConfigKeys.DCA_ALL_OR_NOTHING]:
            dca = DCA(symbol, symbol_pair, base_order_size, safety_order_size, market_price)
            dca.start()
            
            total_cost = dca.total_cost_levels[-1]

            if total_cost > G.available_usd:
                return True

        dca.print_table()
        return False


    def buy(self, symbol: str, symbol_pair: str):
        """Place buy order for symbol_pair."""
        pair         = symbol_pair.split("/")
        order_min    = self.get_order_min('X' + pair[0] + StableCoins.ZUSD) if pair[0] in reg_list else self.get_order_min(pair[0] + pair[1])
        market_price = self.get_bid_price(symbol_pair)

        base_order_size   = self.config.DCA_DATA[symbol][ConfigKeys.DCA_BASE_ORDER_SIZE]
        safety_order_size = self.config.DCA_DATA[symbol][ConfigKeys.DCA_SAFETY_ORDER_SIZE]

        max_price_prec    = self.get_max_price_precision(pair[0]+pair[1])
        max_volume_prec   = self.get_max_volume_precision(pair[0]+pair[1])
        base_order_size   = self.round_decimals_down(base_order_size, max_volume_prec)
        safety_order_size = self.round_decimals_down(safety_order_size, max_volume_prec)
        market_price      = round(market_price, max_price_prec)

        if base_order_size < order_min:
            G.log.print_and_log(f"{symbol} Base order size must be at least {order_min}", G.print_lock)
            return {'status': f'Base order size must be at least {order_min}'}
        if safety_order_size < order_min:
            G.log.print_and_log(f"{symbol} Safety order size must be at least {order_min}", G.print_lock)
            return {'status': f'Safety order size must be at least {order_min}'}

        # if self.config.DCA_DATA[symbol][ConfigKeys.DCA_ALL_OR_NOTHING]:
        #     dca = DCA(symbol, symbol_pair, base_order_size, safety_order_size, market_price)
        #     dca.start()
            
        #     total_cost = dca.total_cost_levels[-1]
        #     if total_cost > G.available_usd:
        #         return {'status': 'DCA_ALL_OR_NOTHING'}

        if self.all_or_nothing(symbol, symbol_pair, base_order_size, safety_order_size, market_price):
            return {'status': 'DCA_ALL_OR_NOTHING'}

        order_result = self.market_order(Trade.BUY, base_order_size, pair[0]+pair[1])
        
        # sleep so kraken exchange can create the data
        time.sleep(1)

        if self.has_result(order_result):
            G.log.print_and_log(f"{symbol_pair} Base order placed {order_result[Dicts.RESULT][Dicts.DESCR][Dicts.ORDER]}", G.print_lock)
            
            entry_price = self.get_entry_price(order_result)
            self.dca    = DCA(symbol, symbol_pair, base_order_size, safety_order_size, entry_price)
            
            self.dca.start()
            self.dca.store_in_db()
            self.dca.print_table()
        else:
            G.log.print_and_log(f"Error: order did not go through! {order_result}", G.print_lock)
            return {'status': f"order did not go through! {order_result}"}
        return {'status': 'ok', 'order_result': order_result}

    def sell(self, symbol_pair_s: str):
        """place a limit order for the base order."""

        symbol_pair = symbol_pair_s.split("/")
        symbol_pair = symbol_pair[0] + symbol_pair[1]

        max_price_prec  = self.get_max_price_precision(symbol_pair)
        max_volume_prec = self.get_max_volume_precision(symbol_pair)

        base_target_price = round(self.dca.base_target_price, max_price_prec)
        base_order_size   = self.round_decimals_down(self.dca.base_order_size, max_volume_prec)

        # place the sell order!
        sell_order_result = self.limit_order(Trade.SELL, base_order_size, symbol_pair, base_target_price)

        if self.has_result(sell_order_result):
            sell_order_txid = sell_order_result[Dicts.RESULT][Data.TXID][0]
            self.mdb.base_order_place_sell(symbol_pair_s, sell_order_txid)
            G.log.print_and_log(f"{symbol_pair_s} Base order placed {sell_order_result[Dicts.RESULT][Dicts.DESCR][Dicts.ORDER]}", G.print_lock)
            return {'status': 'ok'}
        
        G.log.print_and_log(f"Could not place sell order for {symbol_pair}: {sell_order_result}")
        return{'status': 'could not place sell order'}

    def cancel_sell(self):
        """If a safety order has filled while the base sell order has not filled, cancel the base sell order"""
        return


"""
safety order number  deviation_percentage  quantity  total_quantity       price  average_price  required_price  required_change_percentage    profit        cost  total_cost
                  1              1.300000  0.010000        0.020000  220.900470     222.355235      223.467011                    1.161854  0.022090    2.209005    4.447105
                  2              3.328000  0.025000        0.045000  216.361603     219.025440      220.120567                    1.737352  0.048681    5.409040    9.856145
                  3              6.491680  0.062500        0.107500  209.280971     213.360051      214.426851                    2.458838  0.112489   13.080061   22.936205
                  4             11.427021  0.156250        0.263750  198.235185     204.399822      205.421821                    3.625308  0.261423   30.974248   53.910453
                  5             19.126152  0.390625        0.654375  181.003758     190.433690      191.385859                    5.735848  0.592222   70.704593  124.615046
                  6             31.136798  0.976562        1.630937  154.122733     168.691644      169.535102                   10.000062  1.256823  150.510481  275.125527
                  7             49.873405  2.441406        4.072344  112.188333     134.817407      135.491494                   20.771466  2.284347  273.897298  549.022825

"""