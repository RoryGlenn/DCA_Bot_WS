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
# would we make more money buying coins that are a normal buy or a strong sell? With a strong sell, we could get more money with DCA instead of just a buy

# x_list   = ['XETC', 'XETH', 'XLTC', 'XMLN', 'XREP', 'XXBT', 'XXDG', 'XXLM', 'XXMR', 'XXRP', 'XZEC']
# reg_list = ['ETC',  'ETH',  'LTC',  'MLN',  'REP',  'XBT',  'XDG',  'XLM',  'XMR',  'XRP',  'ZEC']


class KrakenDCABot(KrakenBotBase):
    def __init__(self) -> None:
        super().__init__(g_config.API_KEY, g_config.API_SECRET)
        self.rest_api:      KrakenRestAPI = KrakenRestAPI(g_config.API_KEY, g_config.API_SECRET)
        self.tv:            TradingView   = TradingView()
        self.mdb:           MongoDatabase = MongoDatabase()
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

            if self.tv.is_buy(symbol_pair, g_config.DCA_DATA[symbol][ConfigKeys.DCA_TIME_INTERVALS]):
                if symbol in G.x_dict.keys():
                    buy_dict[symbol] = 'X' + symbol + "/" + StableCoins.ZUSD
                else:
                    buy_dict[symbol] = symbol + "/" + StableCoins.USD
        return buy_dict

    def init_socket_handlers(self, ws_token: str) -> None:
        G.socket_handler_open_orders = OpenOrdersSocketHandler(ws_token)
        G.socket_handler_own_trades  = OwnTradesSocketHandler(ws_token)
        G.socket_handler_balances    = BalancesSocketHandler(ws_token)
        return

    # def get_coin_recommendation(self, symbol_list):
    #     if self.tv.is_buy(symbol_pair, g_config.DCA_DATA[symbol][ConfigKeys.DCA_TIME_INTERVALS]):
    #     return        

    # def init_trading_view_threads(self) -> None:
    #     # for every 10 coins, spin up 1 thread.
    #     thread_list = []
    #     num_threads = len(g_config.DCA_DATA.keys()) // 10
    #     start       = 0
    #     end         = len(g_config.DCA_DATA.keys()) - 1

    #     for i in range(num_threads):
    #         thread_list.append( Thread(target=get_coin_recommendation, args=[symbol_list],) )

    #     for thread in thread_list:
    #         thread.start()

    #     for thread in thread_list:
    #         thread.join()
    #     return

    def start_socket_handler_threads(self) -> None:
        Thread(target=G.socket_handler_open_orders.ws_thread).start()
        Thread(target=G.socket_handler_own_trades.ws_thread).start()
        Thread(target=G.socket_handler_balances.ws_thread).start()
        return

    def nuke(self) -> None:
        self.mdb.c_safety_orders.drop()
        self.cancel_all_orders()
        return

    def start_trade_loop(self) -> None:
        base_order    = BaseOrder(g_config.API_KEY, g_config.API_SECRET)
        safety_orders = SafetyOrder(g_config.API_KEY, g_config.API_SECRET)
        ws_token      = self.get_web_sockets_token()[Dicts.RESULT]["token"]

        self.init_socket_handlers(ws_token)
        self.start_socket_handler_threads()

        # wait for socket handlers to finish initializing
        time.sleep(2)

        self.mdb.c_safety_orders.drop()
        # self.cancel_all_buy_orders()

        # [07/01/2022 22:14:47] XZEC/ZUSD Base order filled buy 0.03500000 ZECUSD @ market
        # [07/01/2022 22:14:50] XZEC/ZUSD Base order placed sell 0.03500000 ZECUSD @ limit 146.73
        # [07/01/2022 22:14:51] XZEC/ZUSD Could not place safety order 1 {'error': ['EQuery:Unknown asset pair']}
        # [07/01/2022 22:14:52] XZEC/ZUSD Could not place safety order 2 {'error': ['EQuery:Unknown asset pair']}
        # [07/01/2022 22:14:53] XZEC/ZUSD Could not place safety order 3 {'error': ['EQuery:Unknown asset pair']}
        # [07/01/2022 22:14:54] XZEC/ZUSD Could not place safety order 4 {'error': ['EQuery:Unknown asset pair']}
        # [07/01/2022 22:14:55] XZEC/ZUSD Could not place safety order 5 {'error': ['EQuery:Unknown asset pair']}
        # [07/01/2022 22:14:57] XZEC/ZUSD Could not place safety order 6 {'error': ['EQuery:Unknown asset pair']}
        # [07/01/2022 22:14:58] XZEC/ZUSD Could not place safety order 7 {'error': ['EQuery:Unknown asset pair']}

        while True:
            start_time     = time.time()
            buy_dict       = self.get_buy_dict()
            current_trades = self.mdb.get_current_trades()

            G.log.print_and_log(Color.FG_BRIGHT_BLACK + f"Main thread: checked all coins in {self.get_elapsed_time(start_time)}" + Color.ENDC, G.print_lock)
            G.log.print_and_log(f"Main thread: Current trades {current_trades}", G.print_lock)
            G.log.print_and_log(f"Main thread: Buy list {PrettyPrinter(indent=1).pformat([symbol_pair for (_, symbol_pair) in buy_dict.items()])}", G.print_lock)            

            for symbol, symbol_pair in buy_dict.items():
                if not self.mdb.in_safety_orders(symbol_pair):
                    if self.is_ok(base_order.buy(symbol, symbol_pair)):
                        base_order.sell(symbol_pair)
                        safety_orders.buy(symbol, symbol_pair)
            
            self.wait(message=Color.FG_BRIGHT_BLACK + f"Main thread: waiting until {self.get_buy_time()} to buy" + Color.ENDC, timeout=60)
        return
