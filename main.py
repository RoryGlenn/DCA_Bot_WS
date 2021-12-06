# https://support.kraken.com/hc/en-us/articles/360043283472-Python-WebSocket-recommended-Python-library-and-usage-examples

# https://github.com/krakenfx/kraken-wsclient-py/blob/master/kraken_wsclient_py/kraken_wsclient_py.py


import time
import threading

from bot_features import *

# from bot_features.kraken_rest_api import KrakenRestAPI
from bot_features.kraken_rest_api import *
from bot_features.kraken_enums    import *

from socket_handlers.open_orders_socket_handler import OpenOrdersSocketHandler
from socket_handlers.own_trades_socket_handler  import OwnTradesSocketHandler
from socket_handlers.balances_socket_handler    import BalancesSocketHandler

if __name__ == '__main__':
    kapi = KrakenRestAPI(key=KRAKEN_API_KEY, secret=KRAKEN_SECRET_KEY)

    ws_token1 = kapi.get_web_sockets_token()['result']['token']
    ws_token2 = kapi.get_web_sockets_token()['result']['token']
    ws_token3 = kapi.get_web_sockets_token()['result']['token']
    
    # sh_open_orders = OpenOrdersSocketHandler(ws_token1)
    sh_own_trades = OwnTradesSocketHandler(ws_token2)
    # sh_balances = BalancesSocketHandler(ws_token3)
    
    # threading.Thread(target=sh_open_orders.ws_thread).start()
    threading.Thread(target=sh_own_trades.ws_thread).start()
    # threading.Thread(target=sh_balances.ws_thread).start()

    while True:
        time.sleep(5)
        print("Main thread: %d" % time.time())
        