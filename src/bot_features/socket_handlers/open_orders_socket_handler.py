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

    def __update_available_usd(self, cost: float, msg: str) -> None:
        G.usd_lock.acquire()
        G.available_usd += cost
        G.log.print_and_log(f"openOrders: {msg} -> Available USD: {G.available_usd}", G.print_lock)
        G.usd_lock.release()
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

                    if order_info['descr']['type'] == 'buy':
                        price    = float(order_info['descr']['price'])
                        quantity = float(order_info['vol'])
                        cost     = price * quantity

                        self.__update_available_usd(-cost, "Add up total cost of current open orders")
        elif "openOrders" in message and message[-1]['sequence'] >= 2:
            """We have a new order"""
            for open_orders in message[0]:
                for txid, order_info in open_orders.items():
                    if Status.STATUS in order_info.keys():
                        if order_info[Status.STATUS] == Status.PENDING:
                            self.open_orders[txid] = order_info
                            
                            if order_info['descr']['type'] == 'buy':
                                price    = float(order_info['descr']['price'])
                                quantity = float(order_info['vol'])
                                cost     = price * quantity
                                self.__update_available_usd(-cost, "status pending")
                        elif order_info[Status.STATUS] == Status.CANCELED:
                            # if txid in self.open_orders.keys():
                            price = float(self.open_orders[txid]['descr']['price'])
                            vol   = float(self.open_orders[txid]['vol'])
                            cost  = price * vol
                            self.__update_available_usd(cost, "Cancelled order")
                        elif order_info[Status.STATUS] == Status.OPEN:
                            # G.log.print_and_log(f"openOrders: status open -> Available USD: {G.available_usd}", G.print_lock)
                            G.log.print_and_log(f"openOrders: status open -> message: {message}", G.print_lock)
                        elif order_info[Status.STATUS] == Status.CLOSED:
                            # a buy limit order was filled
                            G.log.print_and_log(f"openOrders: status closed -> {order_info}", G.print_lock)
                    else:
                        # an order was filled
                        #  [[{'OAHGRQ-3CBY3-FCRPDC': {'vol_exec': '0.30000000', 'cost': '5.38200', 'fee': '0.00861', 'avg_price': '17.94000', 'userref': 0}}], 'openOrders', {'sequence': 2}]
                        G.log.print_and_log(f"openOrders: an order was filled -> {message}", G.print_lock)
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
        