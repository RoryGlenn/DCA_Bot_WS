#!/usr/bin/env python

# https://github.com/krakenfx/kraken-wsclient-py

# if using a venv, you must install a new package using this cmd
# python -m pip install package_name

import sys
import signal
import websocket
import json
import datetime
import threading

from pprint          import pprint
from kraken_enums    import *
from kraken_rest_api import KrakenRestAPI



event = threading.Event()

def signal_handler(signalnumber: int, frame) -> None:
    print("KeyboardInterrupt triggered!")
    sys.exit(1)
    
def get_time_now() -> datetime:
    return datetime.datetime.now()

class KrakenWebsocketAPI():
    def get_subscription_data(api_feed: str, api_token: str) -> str:
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
    

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    
    kapi              = KrakenRestAPI(key=KRAKEN_API_KEY, secret=KRAKEN_SECRET_KEY)
    ws_token = kapi.get_web_sockets_token()['result']['token']
    request_data      = KrakenWebsocketAPI.get_subscription_data("openOrders", ws_token)
    
    ws = websocket.create_connection(url=WS_API.API_DOMAIN_PRIVATE)
    ws.send(payload=request_data)
    
    while True:
        try:
            websocket_data = json.loads(ws.recv())
            
            # if the event we are looking for is in the websocket_data, post the event
            """post_event('new_trade', trade)"""
            
            print(f"[{get_time_now()}] {websocket_data}")
        except KeyboardInterrupt:
            ws.close()
            sys.exit(0)
        except Exception as error:
            print(error)
            
    sys.exit(1)
    