import json

from pprint                                           import pprint
from websocket._app                                   import WebSocketApp
from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.low_level.kraken_enums              import *
from util.globals                                     import G


class OpenOrdersSocketHandler(SocketHandlerBase):
    def __init__(self, api_token: str) -> None:
        self.api_token   = api_token
        self.open_orders = { }
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)
        
        if isinstance(message, dict):
            if "heartbeat" in message.values():
                return

        if "openOrders" in message and message[-1]['sequence'] == 1:
            """add up total cost of all the current open orders on startup only!"""
            for open_orders in message[0]:
                for txid, order_info in open_orders.items():
                    self.open_orders[txid] = order_info
        elif "openOrders" in message and message[-1]['sequence'] >= 2:
            """We have a new order"""
            for open_orders in message[0]:
                for txid, order_info in open_orders.items():
                    if Status.STATUS in order_info.keys():
                        if order_info[Status.STATUS] == Status.PENDING:
                            # order is pending
                            self.open_orders[txid] = order_info
                        elif order_info[Status.STATUS] == Status.CANCELED:
                            # order was cancelled
                            pass
                        elif order_info[Status.STATUS] == Status.OPEN:
                            # order is open
                            pass
                        elif order_info[Status.STATUS] == Status.CLOSED:
                            # 1. a buy limit order was filled,
                            # 2. the order status is closed
                                # example -> [13/01/2022 07:49:30] openOrders: status closed -> {'lastupdated': '1642073160.668600', 'status': 'closed', 'vol_exec': '78.12499999', 'cost': '61.3906250', 'fee': '0.0982250', 'avg_price': '0.7858000', 'userref': 0, 'cancel_reason': 'Insignificant volume remaining'}
                            pass
                    else:
                        # an order was filled
                            # example -> [[{'OAHGRQ-3CBY3-FCRPDC': {'vol_exec': '0.30000000', 'cost': '5.38200', 'fee': '0.00861', 'avg_price': '17.94000', 'userref': 0}}], 'openOrders', {'sequence': 2}]
                        pass
        return

    def ws_open(self, ws: WebSocketApp) -> None:
        G.log.print_and_log("openOrders: opened socket", G.print_lock)
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' % {"feed":"openOrders", "token": self.api_token}
        ws.send(api_data)
        return

    def ws_close(self, ws: WebSocketApp, close_status_code: int, close_msg: str) -> None:
        G.log.print_and_log(f"openOrders: closed socket, status code: {close_status_code}, close message:{close_msg}", G.print_lock)
        return

    def ws_error(self, ws: WebSocketApp, error_message: str) -> None:
        G.log.print_and_log("openOrders Error: " + str(error_message), G.print_lock)
        return
        