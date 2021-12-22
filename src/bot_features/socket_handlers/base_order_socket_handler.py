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
        self.api_token:  str          = api_token
        self.ws:         WebSocketApp = None
        self.db:         MongoClient  = MongoClient()[DB.DATABASE_NAME]
        self.collection: Collection   = self.db[DB.COLLECTION_AO]
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        # Success
        # {"descr":"buy 0.00200000 XBTUSD @ limit 9857.0 with 5:1 leverage","event":"addOrderStatus","status":"ok","txid":"OPOUJF-BWKCL-FG5DQL"}
        
        # Error
        # {"errorMessage":"EOrder:Order minimum not met","event":"addOrderStatus","status":"error"}

        message = json.loads(message)
        
        if isinstance(message, dict):
            if message["event"] == "addOrderStatus" and message['status'] == 'ok':
                for key, value in message.items():
                    pprint(message)
            if message["event"] == "addOrderStatus" and message['status'] == 'error':
                pprint(message)
        return
            
    def ws_open(self, ws: WebSocketApp) -> None:
        while True:
            G.base_orders_lock.acquire()
            
            while len(G.base_order_queue) > 0:
                orders = G.base_order_queue[0]
                
                for order in orders:
                    self.ws.send(order)

                G.base_order_queue.pop(0)
            G.base_orders_lock.release()
            time.sleep(1)
        return

    def ws_thread(self, *args) -> None:
        self.ws = WebSocketApp(
            url=WEBSOCKET_PRIVATE_URL,
            on_open=self.ws_open,
            on_message=self.ws_message,
            on_error=self.ws_error)

        self.ws.run_forever()
        return
        