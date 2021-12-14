import json
import pymongo

from pprint                              import pprint
from websocket._app                      import WebSocketApp
from socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.kraken_enums           import *
from util.globals                        import G


class OwnTradesSocketHandler(SocketHandlerBase): 
    def __init__(self, api_token) -> None:
        self.api_token = api_token
        self.trades = dict()
        self.db = pymongo.MongoClient()[DB.DATABASE_NAME]
        self.collection = self.db[DB.COLLECTION_OT]
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)
        
        if isinstance(message, list):
            message = message[0]
            for dictionary in message:
                for txid, trade_info in dictionary.items():
                    self.trades[txid] = trade_info

                    # if its not in the database, add it
                    if self.collection.count_documents({txid: trade_info}) == 0:
                        self.collection.insert_one({txid: trade_info})

                    G.log.pprint_and_log(f"ownTrades: trade", {txid: trade_info}, G.lock)
        else:
            if "heartbeat" not in message.values():
                G.log.pprint_and_log(f"ownTrades: ", message, G.lock)
        return
        
    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' % {"feed":"ownTrades", "token":self.api_token}
        ws.send(api_data)
        return
