import json

from pprint import pprint
from websocket._app                      import WebSocketApp
from socket_handlers.socket_handler_base import SocketHandlerBase

class Status:
    STATUS = "status"
    OPEN = "open"
    PENDING = "pending"
    

class OpenOrdersSocketHandler(SocketHandlerBase):
    def __init__(self, api_token: str) -> None:
        self.api_token: str = api_token
        self.order_que: list = []
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)
        
        if isinstance(message, list):
            for _, dictionary in message[0][0].items():
                if dictionary[Status.STATUS] == Status.PENDING:
                    """we have a new order!"""
                    self.order_que.append(dictionary)
                    for order in self.order_que:
                        pprint(order)
        else:
            pprint(message)
        print()
        return

    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = (
            '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}'
            % {"feed":"openOrders", "token": self.api_token})
        ws.send(api_data)
        return