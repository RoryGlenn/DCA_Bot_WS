import json

from websocket._app      import WebSocketApp
from socket_handlers.socket_handler_base import SocketHandlerBase

class OwnTradesSocketHandler(SocketHandlerBase): 
    def __init__(self, api_token) -> None:
        self.api_token = api_token
        self.trades = dict()
        self.trade_txids = set()

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)
        if isinstance(message, list):
            message = message[0]
            for dictionary in message:
                for txid, trade_info in dictionary.items():
                    self.trades[txid] = trade_info
                    self.trade_txids.add(txid)
        else:
            print(f"ownTrades: {message}")                    

    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' % {"feed":"ownTrades", "token":self.api_token}
        ws.send(api_data)
