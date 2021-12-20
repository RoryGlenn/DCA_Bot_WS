import json
import pymongo

from pprint                              import pprint
from websocket._app                      import WebSocketApp
from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.low_level.kraken_enums           import *
from util.globals                        import G
from bot_features.dca import DCA
from util.config import Config


class OwnTradesSocketHandler(Config, SocketHandlerBase):
    def __init__(self, api_token) -> None:
        self.api_token     = api_token
        self.trades        = dict()
        self.db            = pymongo.MongoClient()[DB.DATABASE_NAME]
        self.collection_ot = self.db[DB.COLLECTION_OT]
        self.collection_os = self.db[DB.COLLECTION_OS]
        self.count         = 0
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)
        if self.count > 3: # only get new trades, not previous ones

            if isinstance(message, list):
                message = message[0]
                
                # [{'T6TB7M-VIU7J-S6XT2Z': {'cost': '4.239200',
                #                           'fee': '0.010174',
                #                           'margin': '0.000000',
                #                           'ordertxid': 'OYN4IA-6PUMX-UTZZKI',
                #                           'ordertype': 'market',
                #                           'pair': 'SC/USD',
                #                           'postxid': 'TKH2SE-M7IF5-CFI7LT',
                #                           'price': '0.015140',
                #                           'time': '1639784469.672391',
                #                           'type': 'buy',
                #                           'vol': '280.00000000'}}]
                for dictionary in message:
                    for txid, trade_info in dictionary.items():
                        self.trades[txid] = trade_info

                        # if its not in the database, add it
                        if self.collection_ot.count_documents({txid: trade_info}) == 0:
                            self.collection_ot.insert_one({txid: trade_info})
                        
                        data        = str(trade_info['pair']).split("/")
                        symbol      = data[0]
                        symbol_pair = data[0] + data[1]

                        # if it is a buy, and not in the database, insert into open symbols table and create safety order table
                        if self.collection_os.count_documents({"symbol_pair": symbol_pair}) == 0:
                            self.collection_os.insert_one({"symbol_pair": symbol_pair})
                            dca = DCA(symbol, symbol_pair, self.BASE_ORDER_SIZE, self.SAFETY_ORDER_SIZE, trade_info['price'])
                            dca.start()

                        G.log.pprint_and_log(f"ownTrades: trade", {txid: trade_info}, G.lock)
            else:
                if "heartbeat" not in message.values():
                    G.log.pprint_and_log(f"ownTrades: ", message, G.lock)
        self.count += 1
        return
        
    def ws_open(self, ws: WebSocketApp) -> None:
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' % {"feed":"ownTrades", "token":self.api_token}
        ws.send(api_data)
        return
