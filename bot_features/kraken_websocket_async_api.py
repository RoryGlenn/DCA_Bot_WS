# https://support.kraken.com/hc/en-us/articles/360043283472-Python-WebSocket-recommended-Python-library-and-usage-examples
# https://github.com/krakenfx/kraken-wsclient-py/blob/master/kraken_wsclient_py/kraken_wsclient_py.py

import websocket
import threading
import time
import sys
import json

from websocket._app       import WebSocketApp
from kraken_websocket_api import KrakenRestAPI
from kraken_enums         import *

API_PRIVATE = {"openOrders", "ownTrades", "balances"}
API_TRADING = {"addOrder", "cancelOrder", "cancelAll", "cancelAllOrdersAfter"}


"""
TODO:
    1. Create a daemon thread that is always reading the config.json file
    2. 
"""

class KrakenWebsocket:
    def __init__(self) -> None:
        self.subscription = str()
    
    # Define WebSocket callback functions
    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        print("WebSocket thread: %s" % message)

    def ws_open(self, ws: WebSocketApp) -> None:
        print("Opened websocket")
        ws.send(self.subscription)
        
    def ws_error(self, ws: WebSocketApp, error_message: str) -> None:
        print(error_message)

    def ws_thread(self, *args) -> None:
        for i in args:
            self.subscription = i
            
        ws = websocket.WebSocketApp(
            url="wss://ws-auth.kraken.com/",
            on_open=self.ws_open,
            on_message=self.ws_message,
            on_error=self.ws_error)
        ws.run_forever()
        
    def get_subscription_data(self, api_feed: str, api_token: str) -> str:
        if api_feed in WS_API.API_PRIVATE:
            # api_private  = {"openOrders", "ownTrades", "balances"}
            api_data = { "event": "subscribe","subscription": {"name": f"{api_feed}", "token": f"{api_token}"} }
        elif api_feed in WS_API.API_TRADING:
            # api_trading  = {"addOrder", "cancelOrder", "cancelAll", "cancelAllOrdersAfter"}
            api_data = '{"event":"%(feed)s", "token":"%(token)s"' % {"feed": api_feed, "token": api_token}
            for count in range(2, len(sys.argv)):
                if sys.argv[count].split('=')[0] == 'txid':
                    api_data = api_data + ', "%(name)s":["%(value)s"]' % {"name": sys.argv[count].split('=')[0], "value": sys.argv[count].split('=')[1].replace(',', '","')}
                elif sys.argv[count].split('=')[0] == 'reqid':
                    api_data = api_data + ', "%(name)s":%(value)s' % {"name": sys.argv[count].split('=')[0], "value": sys.argv[count].split('=')[1]}
                elif sys.argv[count].split('=')[0] == 'timeout':
                    api_data = api_data + ', "%(name)s":%(value)s' % {"name": sys.argv[count].split('=')[0], "value": sys.argv[count].split('=')[1]}
                else:
                    api_data = api_data + ', "%(name)s":"%(value)s"' % {"name": sys.argv[count].split('=')[0], "value": sys.argv[count].split('=')[1]}
            api_data = api_data + '}'
        else:
            print(f"Error: '{api_feed}' is not a valid api_feed")
            sys.exit(1)
        return json.dumps(api_data)


###################################################################################################################
if __name__ == '__main__':
    kapi             = KrakenRestAPI(key=KRAKEN_API_KEY, secret=KRAKEN_SECRET_KEY)
    kwsm_open_orders = KrakenWebsocket()
    kwsm_trades      = KrakenWebsocket()
    kwsm_balances    = KrakenWebsocket()
    
    # threading.Thread(target=read_config, daemon=True).start()
    
    ws_token = kapi.get_web_sockets_token()['result']['token']
    
    open_orders_subscription = kwsm_open_orders.get_subscription_data("openOrders", ws_token)
    own_trades_subscription  = kwsm_trades.get_subscription_data("ownTrades",       ws_token)
    balances_subscription    = kwsm_balances.get_subscription_data("balances",      ws_token)
    
    threading.Thread(target=kwsm_open_orders.ws_thread, args=[open_orders_subscription]).start()
    threading.Thread(target=kwsm_trades.ws_thread, args=[own_trades_subscription]).start()
    threading.Thread(target=kwsm_balances.ws_thread, args=[balances_subscription]).start()

    # Continue other (non WebSocket) tasks in the main thread
    while True:
        time.sleep(5)
        print("Main thread: %d" % time.time())