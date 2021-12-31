import time
import json
import pymongo

from pprint                                           import pprint
from websocket._app                                   import WebSocketApp

from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.low_level.kraken_enums              import *
from bot_features.dca                                 import DCA

from util.globals                                     import G
from util.config                                      import Config


class OwnTradesSocketHandler(SocketHandlerBase):
    def __init__(self, api_token) -> None:
        self.api_token     = api_token

        self.trades        = dict()
        self.config        = Config()
        self.db            = pymongo.MongoClient()[DB.DATABASE_NAME]
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
        if self.count > 3: # only get new trades, not previous ones

            if isinstance(message, list):
                message = message[0]
                
                for dictionary in message:
                    for txid, trade_info in dictionary.items():
                        self.trades[trade_info['ordertxid']] = trade_info

                        # if its not in the database, add it
                        # if self.collection_ot.count_documents({txid: trade_info}) == 0:
                        #     self.collection_ot.insert_one({txid: trade_info})
                        
                        data        = str(trade_info['pair']).split("/")
                        symbol      = data[0]
                        symbol_pair = data[0] + data[1]

                        # if it is a buy, and not in the database, insert into open symbols table and create safety order table
                        # if self.collection_os.count_documents({"symbol_pair": symbol_pair}) == 0:
                        #     self.collection_os.insert_one({"symbol_pair": symbol_pair})
                            # dca = DCA(symbol, symbol_pair, self.config.BASE_ORDER_SIZE, self.config.SAFETY_ORDER_SIZE, trade_info['price'])
                            # dca.start()

                        G.log.pprint_and_log(f"ownTrades: trade", {txid: trade_info}, G.print_lock)
            else:
                if "heartbeat" not in message.values():
                    G.log.pprint_and_log(f"ownTrades: ", message, G.print_lock)
        self.count += 1
        return
        
    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' % {"feed":"ownTrades", "token":self.api_token}
        ws.send(api_data)
        return
