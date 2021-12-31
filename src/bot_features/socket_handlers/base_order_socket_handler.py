import json
import time

from pprint                                           import pprint
from websocket._app                                   import WebSocketApp
from pymongo.mongo_client                             import MongoClient
from pymongo.collection                               import Collection

from bot_features.low_level.kraken_enums              import *
from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase
from util.globals                                     import G


class BaseOrderSocketHandler(SocketHandlerBase):
    def __init__(self, api_token: str) -> None:
        self.api_token:         str          = api_token
        self.buy_order_result:  dict         = {}
        self.sell_order_result: dict         = {}        
        self.ws:                WebSocketApp = None
        self.db:                MongoClient  = MongoClient()[DB.DATABASE_NAME]
        self.collection:        Collection   = self.db[DB.COLLECTION_AO]
        return

    def is_buy_order_ok(self) -> bool:
        print("self.buy_order_result:", self.buy_order_result)
        while 'status' not in self.buy_order_result.keys():
            time.sleep(1)

        return self.buy_order_result['status'] == 'ok'

    def is_sell_order_ok(self) -> bool:
        print("self.sell_order_result:", self.sell_order_result)

        while 'status' not in self.sell_order_result.keys():
            time.sleep(1)

        return self.sell_order_result['status'] == 'ok'


    def ws_buy_sync(self, ws_token: str, symbol_pair: str, order_type: str, base_order_size: float, price: float = 0.0) -> None:
        if order_type == "market":
            buy_base_order = '{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "volume":"%(volume)s"}' \
                % {"feed": "addOrder", "token": ws_token, "pair": symbol_pair, "type": "buy", "ordertype": "market", "volume": base_order_size}
        elif order_type == "limit":
            buy_base_order = '{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "price":"%(price)s, "volume":"%(volume)s"}' \
                % {"feed": "addOrder", "token": ws_token, "pair": symbol_pair, "type": "buy", "ordertype": "limit", "price": price, "volume": base_order_size}

        self.ws.send(buy_base_order)
    
        while len(self.buy_order_result) == 0:
            time.sleep(0.05)
        return

    def ws_sell_sync(self, ws_token: str, symbol_pair: str, price: float, base_order_size: float) -> None:
        sell_base_order = '{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "price":"%(price)s, "volume":"%(volume)s"}' \
            % {"feed": "addOrder", "token": ws_token, "pair": symbol_pair, "type": "sell", "ordertype": "limit", "price": price, "volume": base_order_size}

        self.ws.send(sell_base_order)
    
        while 'status' not in self.sell_order_result.keys():
            time.sleep(0.05)
        return

    def ws_message(self, ws: WebSocketApp, message: dict | list) -> None:
        message = json.loads(message)

        # Success
        # {"descr":"buy 0.00200000 XBTUSD @ limit 9857.0 with 5:1 leverage","event":"addOrderStatus","status":"ok","txid":"OPOUJF-BWKCL-FG5DQL"}
        
        # Error
        # {"errorMessage":"EOrder:Order minimum not met","event":"addOrderStatus","status":"error"}

        if isinstance(message, dict):
            if message["event"] == "addOrderStatus":
                type = message['descr'].split(" ")[0]
                if type == 'buy':
                    self.buy_order_result = message

        elif isinstance(message, list):
            if "openOrders" in message and message[-1]['sequence'] == 2:
                for open_orders in message[0]:
                    for txid, order_info in open_orders.items():
                        if order_info[Status.STATUS] == Status.PENDING or order_info[Status.STATUS] == Status.OPEN:
                            if order_info['descr']['type'] == 'sell':
                                self.sell_order_result = order_info
        return
            
    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' \
            % {"feed":"openOrders", "token": self.api_token}
        
        ws.send(api_data)
        return

    def ws_close(self, ws: WebSocketApp) -> None:
        print("Base socket handler has closed connection...")
        return

    def ws_error(self, ws: WebSocketApp, error_message: str) -> None:
        print("Error: base order socket handler", error_message)
        return

    def ws_thread(self, *args) -> None:
        self.ws = WebSocketApp(
            url=WEBSOCKET_PRIVATE_URL,
            on_open=self.ws_open,
            on_close=self.ws_close,
            on_message=self.ws_message,
            on_error=self.ws_error)
        self.ws.run_forever()
        return
        