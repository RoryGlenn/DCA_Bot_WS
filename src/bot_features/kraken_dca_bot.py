import os

from threading import Thread
from pprint import pprint

from bot_features.buy import Buy
from bot_features.sell import Sell
from bot_features.kraken_bot_base import KrakenBotBase
from bot_features.kraken_enums import *
from bot_features.tradingview import TradingView

from socket_handlers.open_orders_socket_handler import OpenOrdersSocketHandler
from socket_handlers.own_trades_socket_handler import OwnTradesSocketHandler
from socket_handlers.balances_socket_handler import BalancesSocketHandler

from util.config_parser import ConfigParser


class KrakenDCABot(KrakenBotBase):
    def __init__(self, api_key, api_secret) -> None:
        super().__init__(api_key, api_secret)
        self.ta = TradingView()
        self.buy = Buy()
        # self.sell = Sell()
    
    def start(self):
        os.system("cls")
        
        ws_token = self.get_web_sockets_token()["result"]["token"]

        sh_open_orders = OpenOrdersSocketHandler(ws_token)
        sh_own_trades = OwnTradesSocketHandler(ws_token)
        sh_balances = BalancesSocketHandler(ws_token)

        Thread(target=ConfigParser.config_values_loop, daemon=True).start()
        # Thread(target=sh_open_orders.ws_thread).start()
        # Thread(target=sh_own_trades.ws_thread).start()
        # Thread(target=sh_balances.ws_thread).start()
        
        while True:
            for symbol in Buy_.SET:
                alt_name = self.get_alt_name(symbol) 
                symbol_pair = alt_name + StableCoins.USD
                if self.ta._is_buy(symbol_pair):
                    print(symbol_pair)

            # print(f"[{datetime.datetime.now()}] Main thread {result}")        