# https://support.kraken.com/hc/en-us/articles/360043283472-Python-WebSocket-recommended-Python-library-and-usage-examples

# https://github.com/krakenfx/kraken-wsclient-py/blob/master/kraken_wsclient_py/kraken_wsclient_py.py


import time
import datetime
import os

from threading import Thread
from pprint import pprint

from bot_features.kraken_rest_api import KrakenRestAPI
from bot_features.kraken_enums import *

from socket_handlers.open_orders_socket_handler import OpenOrdersSocketHandler
from socket_handlers.own_trades_socket_handler import OwnTradesSocketHandler
from socket_handlers.balances_socket_handler import BalancesSocketHandler
from util.config_parser import ConfigParser


if __name__ == "__main__":
    os.system("cls")
    kapi = KrakenRestAPI(key=KRAKEN_API_KEY, secret=KRAKEN_SECRET_KEY)

    ws_token = kapi.get_web_sockets_token()["result"]["token"]

    sh_open_orders = OpenOrdersSocketHandler(ws_token)
    sh_own_trades = OwnTradesSocketHandler(ws_token)
    sh_balances = BalancesSocketHandler(ws_token)

    Thread(target=ConfigParser.assign_enum_values, daemon=True).start()
    Thread(target=sh_open_orders.ws_thread).start()
    # Thread(target=sh_own_trades.ws_thread).start()
    # Thread(target=sh_balances.ws_thread).start()
    
    
    i      = 0
    result = None
    
    while True:
        time.sleep(30)
        if i % 2 == 0:
            # {'error': [], 'result': {'txid': ['OI5WXM-Q6ALV-VMUHOZ'], 'descr': {'order': 'buy 1.00000000 XBTUSD @ limit 1.0'}}}
            result = kapi.limit_order(Trade.BUY, 1, "XBTUSD", 1.0)
            print(result)
        else:
            kapi.cancel_order(result['result']['txid'][0])
        i+=1
        # print(f"[{datetime.datetime.now()}] Main thread {result}")
