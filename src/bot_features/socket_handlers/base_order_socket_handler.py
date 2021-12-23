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
        self.api_token:    str          = api_token
        self.ws:           WebSocketApp = None
        self.db:           MongoClient  = MongoClient()[DB.DATABASE_NAME]
        self.collection:   Collection   = self.db[DB.COLLECTION_AO]
        self.order_result: dict         = {}
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)

        # Success
        # {"descr":"buy 0.00200000 XBTUSD @ limit 9857.0 with 5:1 leverage","event":"addOrderStatus","status":"ok","txid":"OPOUJF-BWKCL-FG5DQL"}
        
        # Error
        # {"errorMessage":"EOrder:Order minimum not met","event":"addOrderStatus","status":"error"}

        if isinstance(message, dict):
            if message["event"] == "addOrderStatus":
                self.order_result = message
        return
            
    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' \
            % {"feed":"openOrders", "token": self.api_token}
        
        ws.send(api_data)
        return

    def ws_thread(self, *args) -> None:
        self.ws = WebSocketApp(
            url=WEBSOCKET_PRIVATE_URL,
            on_open=self.ws_open,
            on_message=self.ws_message,
            on_error=self.ws_error)

        self.ws.run_forever()
        return
        