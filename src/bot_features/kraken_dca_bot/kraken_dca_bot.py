import time

from pprint                                                  import pprint, PrettyPrinter
from threading                                               import Thread

from bot_features.orders.base_order                          import BaseOrder
from bot_features.orders.safety_order                        import SafetyOrder

from bot_features.database.mongo_database                    import MongoDatabase

from bot_features.socket_handlers.balances_socket_handler    import BalancesSocketHandler
from bot_features.socket_handlers.open_orders_socket_handler import OpenOrdersSocketHandler
from bot_features.socket_handlers.own_trades_socket_handler  import OwnTradesSocketHandler

from bot_features.low_level.kraken_rest_api                  import KrakenRestAPI
from bot_features.low_level.kraken_bot_base                  import KrakenBotBase
from bot_features.low_level.kraken_enums                     import *

from bot_features.tradingview.trading_view                   import TradingView

from util.colors                                             import Color
from util.globals                                            import G
from util.config                                             import g_config


class KrakenDCABot(KrakenBotBase):
    def __init__(self) -> None:
        super().__init__(g_config.API_KEY, g_config.API_SECRET)
        self.rest_api     = KrakenRestAPI(g_config.API_KEY, g_config.API_SECRET)
        self.trading_view = TradingView()
        self.mdb          = MongoDatabase()
        return

    def is_ok(self, order_result: dict):
        if isinstance(order_result, dict):
            if 'status' in order_result:
                return order_result['status'] == 'ok'
        return False
    
    def get_buy_dict(self) -> dict:
        """Returns dictionary with [symbol: symbol_pair] relationship"""
        buy_dict = {}

        for symbol in g_config.DCA_DATA:
            alt_name = self.get_alt_name(symbol)

            if alt_name is None:
                continue

            symbol_pair = alt_name + StableCoins.USD

            G.log.print_and_log(f"Main thread: checking {symbol_pair}", G.print_lock)

            if symbol in G.x_list or symbol in G.reg_list: # temp fix until we solve the x_list issue
                continue

            if self.trading_view.is_buy(symbol_pair, g_config.DCA_DATA[symbol][ConfigKeys.DCA_TIME_INTERVALS]):
                if symbol in G.x_dict.keys():
                    buy_dict[G.x_dict[symbol]] = G.x_dict[symbol] + "/" + StableCoins.ZUSD
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

        # wait for socket handlers to finish initializing variables
        time.sleep(3)
        return

    def market_sell_all_assets(self):
        """Maket sells all assets except for staked assets in spot wallet."""
        for symbol, quantity_to_sell in self.get_account_balance()['result'].items():
            quantity_to_sell = float(quantity_to_sell)
            symbol_pair      = ""
            pair             = ""

            if quantity_to_sell == 0:
                continue

            if symbol in StableCoins.STABLE_COINS_LIST:
                continue
        
            if '.' in symbol:
                continue
            
            if symbol in G.x_list:
                symbol_pair = symbol + '/' + StableCoins.ZUSD
                pair        = symbol + StableCoins.ZUSD
            else:
                symbol_pair = symbol + '/' + StableCoins.USD
                pair        = symbol + StableCoins.USD

            pair      = str(symbol_pair).split("/")
            pair = pair[0] + pair[1]
            order_min = self.get_order_min(pair)

            if quantity_to_sell < order_min:
                G.log.print_and_log(f"{symbol} {quantity_to_sell} is too low to sell", G.print_lock)
                continue

            max_volume_prec  = self.get_max_volume_precision(pair)
            quantity_to_sell = self.round_decimals_down(quantity_to_sell, max_volume_prec)

            order_result = self.market_order(symbol_pair, Trade.SELL, quantity_to_sell)
            G.log.print_and_log(f"{order_result}", G.print_lock)
        return

    def nuke(self) -> None:
        G.log.print_and_log("WIPING DATABASE AND OPEN BUY ORDERS!!! You have 10 seconds to cancel...", G.print_lock)
        # time.sleep(10)

        self.mdb.c_safety_orders.drop()

        # cancel all orders in database!
        for txid, order_info in self.get_open_orders()['result']['open'].items():
            # if order_info['descr']['type'] == 'buy':
            self.cancel_order(txid)

        self.market_sell_all_assets()
        G.log.print_and_log("Wipe Complete!", G.print_lock)
        return

    def start_trade_loop(self) -> None:
        base_order    = BaseOrder(g_config.API_KEY, g_config.API_SECRET)
        safety_orders = SafetyOrder(g_config.API_KEY, g_config.API_SECRET)
        ws_token      = self.get_web_sockets_token()[Dicts.RESULT]["token"]

        self.init_socket_handlers(ws_token)
        self.start_socket_handler_threads()

        self.nuke()

        while True: 
            start_time     = time.time()
            buy_dict       = self.get_buy_dict()
            current_trades = self.mdb.get_current_trades()

            G.log.print_and_log(Color.FG_BRIGHT_BLACK + f"Main thread: checked all coins in {self.get_elapsed_time(start_time)}" + Color.ENDC, G.print_lock)
            G.log.print_and_log(f"Main thread: Current trades {len(current_trades)} total: {current_trades}", G.print_lock)
            G.log.print_and_log(f"Main thread: Buy list {len(buy_dict)} total: {PrettyPrinter(indent=1).pformat([symbol_pair for (_, symbol_pair) in buy_dict.items()])}", G.print_lock)

            for symbol, symbol_pair in buy_dict.items():
                if not self.mdb.in_safety_orders(symbol_pair):
                    if self.is_ok(base_order.buy(symbol, symbol_pair)):
                        base_order.sell(symbol_pair)
                        safety_orders.buy(symbol, symbol_pair)
            
            self.wait(message=Color.FG_BRIGHT_BLACK + f"Main thread: waiting until {self.get_buy_time()} to buy\n" + Color.ENDC, timeout=60)
        return
