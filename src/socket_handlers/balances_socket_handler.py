import json
import pymongo

from pprint                              import pprint
from websocket._app                      import WebSocketApp
from socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.kraken_enums           import *
from util.globals                        import G


class BalancesSocketHandler(SocketHandlerBase):
    def __init__(self, api_token) -> None:
        self.api_token = api_token
        self.db = pymongo.MongoClient()[DB.DATABASE_NAME]
        self.collection = self.db[DB.COLLECTION_B]
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)
        
        if isinstance(message, dict):
            if "balances" in message.keys():
                for symbol, quantity in message["balances"].items():
                    if quantity > 0:
                        G.log.print_and_log(f"balances:  {symbol} {quantity}", G.lock)
            else:
                G.log.pprint_and_log(f"balances:  ", message, G.lock)
        else:
            G.log.pprint_and_log(f"balances:  ", message, G.lock)
        return
            
    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = (
            '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}'
            % {"feed": "balances", "token": self.api_token}
        )
        ws.send(api_data)
        return