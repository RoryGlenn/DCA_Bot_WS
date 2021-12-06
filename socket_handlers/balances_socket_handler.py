import json

from websocket._app      import WebSocketApp
from socket_handlers.socket_handler_base import SocketHandlerBase

class BalancesSocketHandler(SocketHandlerBase):
    def __init__(self, api_token) -> None:
        self.api_token = api_token

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)
        if isinstance(message, list):
            message = message[0]
            for dictionary in message:
                for txid, _dict in dictionary.items():
                    print(txid, _dict["descr"])
        else:
            print(f"balances: {message}")

    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' % {"feed":"balances", "token":self.api_token}
        ws.send(api_data)
