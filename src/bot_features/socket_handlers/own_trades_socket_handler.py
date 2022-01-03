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

                                # if the new trade matches a safety order inside of the db, 
                                # cancel the current sell order and place a new one.
                                

                                # is the new trade a buy or a sell
                                # if its a buy, cancel the current sell order and place a new one
                                # if its a sell, cancel all orders associated with the symbol and wipe the db

                                s_symbol_pair = trade_info['pair']
                                order_txid    = trade_info['ordertxid']

                                # query the db to find the safety order associated with s_symbol_pair
                                placed_safety_orders = self.mdb.get_placed_safety_order_data(s_symbol_pair)
                                for safety_order in placed_safety_orders:
                                    if safety_order['order_txid'] == order_txid:
                                        self.mdb.update_filled_safety_order(s_symbol_pair, order_txid)

                                        cancel_result = self.rest_api.cancel_order(...)

                                        if 'result' in cancel_result.keys():
                                            if cancel_result['result']['count'] == 1: # {'error': [], 'result': {'count': 1}}
                                                self.mdb.cancel_sell_order(s_symbol_pair)
                                        
                                        
                                        # cancel the open sell order associated with s_symbol_pair
                                        # place new sell order
                                        pass
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
