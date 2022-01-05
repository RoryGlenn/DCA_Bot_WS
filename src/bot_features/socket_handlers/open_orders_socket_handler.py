import json

from pprint                                           import pprint
from websocket._app                                   import WebSocketApp
from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.low_level.kraken_enums              import *
from util.globals                                     import G


class OpenOrdersSocketHandler(SocketHandlerBase):
    def __init__(self, api_token: str) -> None:
        self.api_token:         str  = api_token
        self.open_orders:       dict = { }
        return

    def ws_error(self, ws: WebSocketApp, error_message: str) -> None:
        G.log.print_and_log("openOrders: " + str(error_message), G.print_lock)
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)
        
        if isinstance(message, dict):
            if "heartbeat" in message.values():
                return
        else:
            if "openOrders" in message and message[-1]['sequence'] == 1:
                """add up total cost of all the current open orders"""
                for open_orders in message[0]:
                    for txid, order_info in open_orders.items():

                        self.open_orders[txid] = order_info

                        if order_info['descr']['type'] == 'buy':
                            price    = float(order_info['descr']['price'])
                            quantity = float(order_info['vol'])
                            cost     = price * quantity

                            G.usd_lock.acquire()
                            G.available_usd -= cost
                            G.available_usd = round(G.available_usd, 8)
                            G.usd_lock.release()
            elif "openOrders" in message and message[-1]['sequence'] >= 2:
                """if we have a new order"""
                for open_orders in message[0]:
                    for txid, order_info in open_orders.items():
                        if Status.STATUS not in order_info.keys():
                            return

                        if order_info[Status.STATUS] == Status.PENDING:
                            self.open_orders[txid] = order_info

                            # subtract the value from G.availableusd
                            if order_info['descr']['type'] == 'buy':
                                price    = float(order_info['descr']['price'])
                                quantity = float(order_info['vol'])
                                cost     = price * quantity

                                G.usd_lock.acquire()
                                G.available_usd -= cost
                                G.available_usd = round(G.available_usd, 8)
                                G.usd_lock.release()
                        elif order_info[Status.STATUS] == Status.CANCELED:
                            if txid in self.open_orders.keys():
                                price     = float(self.open_orders[txid]['descr']['price'])
                                vol       = float(self.open_orders[txid]['vol'])
                                usd_value = price * vol

                                G.usd_lock.acquire()
                                G.available_usd += usd_value
                                G.available_usd = round(G.available_usd, 8)
                                G.usd_lock.release()
                            else:
                                pprint("aiuefhawipawefopiawhfashdfaopfhasdfkajsdfljasdf")
                        elif order_info[Status.STATUS] == Status.OPEN:
                            pass
        return

    def ws_open(self, ws: WebSocketApp) -> None:
        print("openOrders: opened socket")
        
        api_data = (
            '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}'
                % {"feed":"openOrders", "token": self.api_token})
        ws.send(api_data)
        return

    def ws_close(self, ws: WebSocketApp, arg1: str, arg2: str) -> None:
        G.log.print_and_log("Closing openOrders socket", G.print_lock)
        return