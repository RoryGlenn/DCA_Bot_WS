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
        self.collection = self.db[DB.COLLECTION_OO]
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)

        if isinstance(message, dict):
            if "heartbeat" in message.values():
                return

        else:
            """if we have a new order"""
            if "openOrders" in message and message[-1]['sequence'] == 2:
                for open_orders in message[0]:
                    for txid, order_info in open_orders.items():
                        if order_info[Status.STATUS] == Status.PENDING or order_info[Status.STATUS] == Status.OPEN:
                            self.open_orders[txid] = order_info

                            # add symbol_pair to open_symbol_pairs
                            # pair = order_info["descr"]["pair"].split("/")
                            # symbol_pair = pair[0] + pair[1]
                            # self.open_symbol_pairs.add(symbol_pair)

                            # grab the open orders from the data base and store them in self.open_symbol_pairs

                            # if its not in the database, add it
                            if self.collection.count_documents({txid: order_info}) == 0:
                                self.collection.insert_one({txid: order_info})

                            G.log.pprint_and_log(f"openOrders: open order", order_info, G.print_lock)
                        if order_info[Status.STATUS] == Status.CANCELED:
                            self.open_orders.pop(txid)
                            self.collection.delete_one({txid: order_info})

                            pair = order_info["descr"]["pair"].split("/")
                            symbol_pair = pair[0] + pair[1]
                            if symbol_pair in self.open_symbol_pairs:
                                self.open_symbol_pairs.remove(symbol_pair)

                            G.log.pprint_and_log(f"openOrders: canceled order", message, G.print_lock)
            
            elif "openOrders" in message and message[-1]['sequence'] == 1:
                """add up total cost of open orders"""
                for open_orders in message[0]:
                    for txid, order_info in open_orders.items():
                        if order_info['descr']['type'] == 'buy':
                            price    = float(order_info['descr']['price'])
                            quantity = float(order_info['vol'])
                            cost     = price * quantity

                            G.usd_lock.acquire()
                            G.available_usd -= cost
                            G.available_usd = round(G.available_usd, 8)
                            G.usd_lock.release()
        return

    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = (
            '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}'
            % {"feed":"openOrders", "token": self.api_token})
        ws.send(api_data)
        return