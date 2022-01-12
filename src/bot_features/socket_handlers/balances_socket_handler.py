import json

from pprint                                           import pprint
from websocket._app                                   import WebSocketApp

from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.low_level.kraken_enums              import *

from util.globals                                     import G


class BalancesSocketHandler(SocketHandlerBase):
    def __init__(self, api_token: str) -> None:
        self.api_token = api_token
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)
        
        if isinstance(message, dict):
            if "balances" in message.keys():
                G.usd_lock.acquire()
                G.available_usd += float(message['balances']['USD'])
                G.log.print_and_log(f"balances: Available USD: {G.available_usd}", G.print_lock)
                G.usd_lock.release()
        return
            
    def ws_open(self, ws: WebSocketApp) -> None:
        G.log.print_and_log("balances: opened socket", G.print_lock)
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' % {"feed": "balances", "token": self.api_token}
        ws.send(api_data)
        return

    def ws_close(self, ws: WebSocketApp, close_status_code: int, close_msg: str) -> None:
        G.log.print_and_log(f"balances: closed socket, status code: {close_status_code}, close message:{close_msg}", G.print_lock)
        return

    def ws_error(self, ws: WebSocketApp, error_message: str) -> None:
        G.log.print_and_log("balances: Error " + str(error_message), G.print_lock)
        return

    def ws_thread(self, *args) -> None:
        while True:
            ws = WebSocketApp(
                url=WEBSOCKET_PRIVATE_URL,
                on_open=self.ws_open,
                on_close=self.ws_close,
                on_message=self.ws_message,
                on_error=self.ws_error)
            ws.run_forever()
        return