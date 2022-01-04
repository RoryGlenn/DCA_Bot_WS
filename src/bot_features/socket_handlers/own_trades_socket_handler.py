import time
import json
import pymongo

from pprint                                           import pprint
from websocket._app                                   import WebSocketApp

from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.low_level.kraken_enums              import *
from bot_features.low_level.kraken_rest_api           import KrakenRestAPI
from bot_features.database.mongo_database             import MongoDatabase
from util.globals                                     import G
from util.config                                      import Config

class OwnTradesSocketHandler(SocketHandlerBase):
    def __init__(self, api_token) -> None:
        self.api_token: str = api_token

        self.trades        = dict()
        self.config        = Config()
        self.rest_api      = KrakenRestAPI(self.config.API_KEY, self.config.API_SECRET)
        self.mdb           = MongoDatabase()
        self.db            = pymongo.MongoClient()[DB.DATABASE_NAME]
        self.c_safety_orders = self.db[DB.COLLECTION_SO]
        self.collection_ot = self.db[DB.COLLECTION_OT]
        self.collection_os = self.db[DB.COLLECTION_OS]
        self.count         = 0
        return

    def get_entry_price(self, order_txid: str) -> float:
        while order_txid not in self.trades.keys():
            time.sleep(0.05)
            
        return float(self.trades[order_txid]['price'])

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)

        if isinstance(message, list):
            if isinstance(message[-1], dict):
                if 'sequence' in message[-1].keys():
                    if message[-1]['sequence'] == 2:
            
                        message = message[0]
                        
                        for dictionary in message:
                            for txid, trade_info in dictionary.items():
                                self.trades[ trade_info['ordertxid'] ] = trade_info
                                G.log.pprint_and_log(f"ownTrades: New trade found!", {txid: trade_info}, G.print_lock)

                                # "TDLH43-DVQXD-2KHVYY": {
                                #     "cost": "1000000.00000",
                                #     "fee": "1600.00000",
                                #     "margin": "0.00000",
                                #     "ordertxid": "TDLH43-DVQXD-2KHVYY",
                                #     "ordertype": "limit",
                                #     "pair": "XBT/EUR",
                                #     "postxid": "OGTT3Y-C6I3P-XRI6HX",
                                #     "price": "100000.00000",
                                #     "time": "1560516023.070651",
                                #     "type": "sell",
                                #     "vol": "1000000000.00000000"
                                # }

                                s_symbol_pair = trade_info['pair']
                                order_txid    = trade_info['ordertxid']

                                # if its a buy, cancel the current sell order and place a new one
                                if trade_info['type'] == 'buy':
                                    if self.mdb.is_safety_order(s_symbol_pair, order_txid):
                                        placed_safety_orders = self.mdb.get_placed_safety_order_data(s_symbol_pair)
                                        
                                        for safety_order in placed_safety_orders:
                                            if safety_order['order_txid'] == order_txid:
                                                self.mdb.update_filled_safety_order(s_symbol_pair, order_txid)

                                                # figure out which safety order number was just filled (if it was a safety order at all...)
                                                # if safety order number 1 was filled, cancel the base sell order
                                                # if safety order number 2 was filled, cancel safety order 1 sell order...
                                                filled_so_nums = self.mdb.get_filled_safety_order_numbers(s_symbol_pair)

                                                if filled_so_nums[-1] == 1:
                                                    # cancel the base sell order
                                                    base_order_txid = self.mdb.get_base_order_sell_txid(s_symbol_pair)
                                                    cancel_result   = self.rest_api.cancel_order(base_order_txid)
                                                else:
                                                    # cancel the sell limit safety order whose so_num is: filled_so_nums[-1] - 1
                                                    self.rest_api.cancel_order(txid)
                                                    txid = self.mdb.get_safety_order_sell_txid(s_symbol_pair, filled_so_nums[-2])

                                                # value         = self.mdb.get_value(s_symbol_pair, order_txid)
                                                # cancel_result = self.rest_api.cancel_order(...)

                                                # if 'result' in cancel_result.keys():
                                                #     if cancel_result['result']['count'] == 1: # {'error': [], 'result': {'count': 1}}
                                                #         self.mdb.cancel_sell_order(s_symbol_pair)

                                        # cancel the open sell order associated with s_symbol_pair
                                        # place new sell order
                                    else:
                                        """the base order was filled, no need to do anything..."""
                                        pass
                                elif trade_info['type'] == 'sell':
                                    # if its a sell, cancel all orders associated with the symbol and wipe the db
                                    placed_safety_orders = self.mdb.get_placed_safety_order_data(s_symbol_pair)
                                    
                                    # cancel all orders associated with the symbol
                                    for safety_order in placed_safety_orders:
                                        self.rest_api.cancel_order(safety_order['order_txid'])

                                    # remove all data associated with s_symbol_pair from db
                                    self.mdb.c_safety_orders.delete_one({"_id": s_symbol_pair})

                                    # print how much we profited.
        else:
            if isinstance(message, dict):
                if message['event'] == 'systemStatus':
                    return
                if message['event'] == 'subscriptionStatus':
                    return
            if "heartbeat" not in message.values():
                G.log.pprint_and_log(f"ownTrades: ", message, G.print_lock)
        return
        
    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' % {"feed":"ownTrades", "token":self.api_token}
        ws.send(api_data)
        return
