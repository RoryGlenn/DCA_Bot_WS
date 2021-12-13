import json
import pymongo

from pprint                              import pprint
from websocket._app                      import WebSocketApp
from socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.kraken_enums           import *
from util.globals                        import G


class OpenOrdersSocketHandler(SocketHandlerBase):
    def __init__(self, api_token: str) -> None:
        self.api_token:   str = api_token
        self.open_orders: dict = { }
        self.db = pymongo.MongoClient()[DB.DATABASE_NAME]
        self.collection = self.db[DB.COLLECTION_OO]
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)
        
        if isinstance(message, list):
            for open_orders in message[0]:
                for txid, order_info in open_orders.items():
                    if order_info[Status.STATUS] == Status.PENDING or order_info[Status.STATUS] == Status.OPEN:
                        self.open_orders[txid] = order_info
                        
                        # if its not in the database, add it
                        if self.collection.count_documents({txid: order_info}) == 0:
                            self.collection.insert_one({txid: order_info})

                        G.log.pprint_and_log(f"openOrders: open order", order_info, G.lock)
                    if order_info[Status.STATUS] == Status.CANCELED:
                        self.open_orders.pop(txid)
                        self.collection.delete_one({txid: order_info})
                        G.log.pprint_and_log(f"openOrders: canceled order", message, G.lock)
        else:           
            G.log.pprint_and_log("openOrders:", message, G.lock)
        return

    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = (
            '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}'
            % {"feed":"openOrders", "token": self.api_token})
        ws.send(api_data)
        return