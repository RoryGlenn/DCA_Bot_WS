import json
import pymongo

from websocket                           import create_connection
from pprint                              import pprint

from websocket._app                      import WebSocketApp
from bot_features.kraken_enums           import *
from util.globals                        import G


class AddOrderSocketHandler():
    def __init__(self, api_token) -> None:
        self.api_token = api_token
        self.db = pymongo.MongoClient()[DB.DATABASE_NAME]
        self.collection = self.db[DB.COLLECTION_AO]
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)
        pprint(message)

        # if isinstance(message, dict):
            # if "addOrder" in message.keys():
                # for symbol, quantity in message["addOrder"].items():
                #     if quantity > 0:
                #         G.log.print_and_log(f"addOrder:  {symbol} {quantity}", G.lock)
        return
            
    def ws_open(self, **kargs) -> None:
	    # Example: ./krakenws.py addOrder pair=XBT/EUR type=sell ordertype=limit price=7500 volume=0.125
        # '{"event":"addOrder", "token":"W4ytptkui/C8+zBmVQJsspQcnwMSoYil1e7/8WW1aYk", "pair":"XBT/EUR", "type":"sell", "ordertype":"limit", "price":"7500", "volume":"0.125"}'

        # symbol_pair: str, type: str, order_type: str, price: float, quantity: float

        ws = create_connection("wss://ws-auth.kraken.com/")

        if kargs["order_type"] == "limit":
            api_data = '{"event":"%(feed)s", "token":"%(token)s", "pair":"%(symbol_pair)s", "type":"%(type)s", "ordertype":%(ordertype)s, "price":"%(price)s", "volume":%(volume)s}' \
                % {"feed":"addOrder", "token": self.api_token, "pair":kargs["symbol_pair"], "type":kargs["type"], "ordertype":kargs["order_type"], "price":kargs["price"], "volume":kargs["quantity"]} 
                
        if kargs["order_type"] == "market":
            api_data = '{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":%(ordertype)s,  "volume":%(volume)s}' \
                % {"feed":"addOrder", "token": self.api_token, "pair":kargs["symbol_pair"], "type":kargs["type"], "ordertype":kargs["order_type"], "volume":kargs["quantity"]} 
                            
        ws.send(api_data)
        return

