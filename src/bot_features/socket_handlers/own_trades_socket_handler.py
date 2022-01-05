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
from util.config                                      import g_config

class OwnTradesSocketHandler(SocketHandlerBase):
    def __init__(self, api_token) -> None:
        self.api_token: str = api_token

        self.trades        = dict()
        self.rest_api      = KrakenRestAPI(g_config.API_KEY, g_config.API_SECRET)
        self.mdb           = MongoDatabase()
        self.db            = pymongo.MongoClient()[DB.DATABASE_NAME]
        self.c_safety_orders = self.db[DB.COLLECTION_SO]
        self.collection_ot = self.db[DB.COLLECTION_OT]
        self.collection_os = self.db[DB.COLLECTION_OS]
        self.count         = 0
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)

        if isinstance(message, list):
            if isinstance(message[-1], dict):
                if 'sequence' in message[-1].keys():
                    if message[-1]['sequence'] >= 2:
                        message = message[0]
                        
                        for dictionary in message:
                            for txid, trade_info in dictionary.items():
                                self.trades[ trade_info['ordertxid'] ] = trade_info
                                # G.log.pprint_and_log(f"ownTrades: New trade found!", {txid: trade_info}, G.print_lock)

                                s_symbol_pair = trade_info['pair']
                                order_txid    = trade_info['ordertxid']

                                # if its a buy, cancel the current sell order and place a new one
                                if trade_info['type'] == 'buy':

                                    if not self.mdb.is_safety_order(s_symbol_pair, order_txid):
                                        # The base order was filled, no need to do anything...
                                        pass
                                    else:
                                        # A safety order was filled!

                                        placed_safety_orders = self.mdb.get_placed_safety_order_data(s_symbol_pair)
                                        
                                        for safety_order in placed_safety_orders:
                                            if safety_order['order_txid'] == order_txid:
                                                self.mdb.update_filled_safety_order(s_symbol_pair, order_txid)

                                                filled_so_nums = self.mdb.get_filled_safety_order_numbers(s_symbol_pair)

                                                # code below figures out which safety order was filled.

                                                # if filled_so_nums[-1] >= g_config.DCA_DATA[ConfigKeys.DCA_SAFETY_ORDERS_MAX]:
                                                #     return

                                                if filled_so_nums[-1] == 1:
                                                    # the first safety order has filled so cancel the base sell order
                                                    base_order_txid = self.mdb.get_base_order_sell_txid(s_symbol_pair)
                                                    cancel_result   = self.rest_api.cancel_order(base_order_txid)
                                                    
                                                    print(cancel_result)
                                                    # place the first safety order sell

                                                    # get the limit price and the quantity to sell
                                                    so_data  = self.mdb.get_safety_order_data_by_num(s_symbol_pair, filled_so_nums[-1]+1)
                                                    price    = float(so_data['price'])
                                                    quantity = float(so_data['quantity'])

                                                    order_result = self.rest_api.limit_order(Trade.SELL, quantity, s_symbol_pair, price)

                                                    if 'result' in order_result.keys():
                                                        G.log.print_and_log(f"{s_symbol_pair} sell order placed {order_result[Dicts.RESULT]}", G.print_lock)
                                                    else:
                                                        G.log.print_and_log(f"{s_symbol_pair} could not place sell order {order_result}", G.print_lock)
                                                else:
                                                    # cancel the sell limit safety order whose so_num is: filled_so_nums[-1] - 1
                                                    # self.rest_api.cancel_order(txid)
                                                    _txid = self.mdb.get_safety_order_sell_txid(s_symbol_pair, filled_so_nums[-2])
                                                    self.rest_api.cancel_order(_txid)

                                                # value         = self.mdb.get_value(s_symbol_pair, order_txid)
                                                # cancel_result = self.rest_api.cancel_order(...)

                                                # if 'result' in cancel_result.keys():
                                                #     if cancel_result['result']['count'] == 1: # {'error': [], 'result': {'count': 1}}
                                                #         self.mdb.cancel_sell_order(s_symbol_pair)

                                        # cancel the open sell order associated with s_symbol_pair
                                        # place new sell order
                                elif trade_info['type'] == 'sell':
                                    # if its a sell, cancel all orders associated with the symbol and wipe the db
                                    placed_safety_orders = self.mdb.get_placed_safety_order_data(s_symbol_pair)
                                    
                                    # cancel all orders associated with the symbol
                                    for safety_order in placed_safety_orders:
                                        self.rest_api.cancel_order(safety_order['buy_order_txid'])

                                    # remove all data associated with s_symbol_pair from db
                                    self.mdb.c_safety_orders.delete_one({"_id": s_symbol_pair})

                                    # to calculate profit, figure out if we sold the base order or a safety order
                                    # if its a safety order, which one did you sell?
                                    # grab that number from the mdb

                                    # https://www.kraken.com/en-us/features/fee-schedule/#kraken-pro
                                    # CALCULATE PROFIT BY: (EXIT_COST - ENTRY_COST - FEE)
                                    # entry_cost = 2.2774
                                    # exit_cost  = 2.2892
                                    # maker_fee  = 0.0016
                                    # taker_fee  = 0.0026

                                    # profit = exit_cost - entry_cost - maker_fee - taker_fee
                                    G.log.print_and_log(f"{s_symbol_pair} trade complete!")
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

    def ws_error(self, ws: WebSocketApp, error_message: str) -> None:
        print(f"Error ownTrades: {str(error_message)}")
