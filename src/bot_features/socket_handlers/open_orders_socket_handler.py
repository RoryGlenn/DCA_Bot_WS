import json
import pymongo


from pprint                                           import pprint
from websocket._app                                   import WebSocketApp
from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.low_level.kraken_enums              import *
from util.globals                                     import G


class OpenOrdersSocketHandler(SocketHandlerBase):
    def __init__(self, api_token: str) -> None:
        self.api_token:   str = api_token
        self.open_orders: dict = { }
        self.open_symbol_pairs = set()
        self.count: int = 0

        self.db = pymongo.MongoClient()[DB.DATABASE_NAME]
        self.c_open_orders  = self.db[DB.COLLECTION_OO]
        self.c_open_symbols = self.db[DB.COLLECTION_OS]
        self.c_safety_orders = self.db[DB.COLLECTION_SO]
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
                        if order_info['descr']['type'] == 'buy':
                            price    = float(order_info['descr']['price'])
                            quantity = float(order_info['vol'])
                            cost     = price * quantity

                            G.usd_lock.acquire()
                            G.available_usd -= cost
                            # print("sequence 1:")
                            G.available_usd = round(G.available_usd, 8)
                            G.usd_lock.release()
            elif "openOrders" in message and message[-1]['sequence'] == 2:
                """if we have a new order"""
                for open_orders in message[0]:
                    for txid, order_info in open_orders.items():
                        if order_info[Status.STATUS] == Status.PENDING or order_info[Status.STATUS] == Status.OPEN:
                            self.open_orders[txid] = order_info
                            
                            # subtract the value from G.availableusd
                            price    = float(order_info['descr']['price'])
                            quantity = float(order_info['vol'])
                            cost     = price * quantity

                            G.usd_lock.acquire()
                            G.available_usd -= cost
                            G.available_usd = round(G.available_usd, 8)
                            # print("sequence 2:")
                            # print("openOrders: G.available_usd", G.available_usd)
                            G.usd_lock.release()
            elif "openOrders" in message and message[-1]['sequence'] == 3:

                # this block of code is for an orders status change!

                """
                    [
                        {'OFMGU4-U3SPH-JWD5SO': {'status': 'open', 'userref': 0}}
                    ], 
                    
                    'openOrders',

                    {'sequence': 3}
                """

                # print("sequence 3:", message[0])
                return
                      
        return

    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = (
            '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}'
            % {"feed":"openOrders", "token": self.api_token})
        ws.send(api_data)
        return