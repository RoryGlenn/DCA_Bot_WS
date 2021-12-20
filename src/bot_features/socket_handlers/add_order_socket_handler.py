import json

from pymongo.mongo_client                import MongoClient
from pymongo.collection                  import Collection

from websocket                           import WebSocket, create_connection
from pprint                              import pprint

from websocket._app                      import WebSocketApp
from bot_features.low_level.kraken_enums import *
from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase
from util.globals                        import G


class AddOrderSocketHandler(SocketHandlerBase):
    def __init__(self, api_token: str) -> None:
        self.api_token:  str         = api_token
        self.ws:         WebSocket   = None
        self.db:         MongoClient = MongoClient()[DB.DATABASE_NAME]
        self.collection: Collection  = self.db[DB.COLLECTION_AO]
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        """
        Response example

        {
            "descr": "buy 0.01770000 XBTUSD @ limit 4000",
            "event": "addOrderStatus",
            "status": "ok",
            "txid": "ONPNXH-KMKMU-F4MR5V"
        }

        """        
        
        message = json.loads(message)
        
        if isinstance(message, dict):
            if message["event"] == "addOrderStatus":
                for key, value in message.items():
                    print(key, value)
        return
            
    def ws_open(self, ws: WebSocketApp) -> None:
        print("Opened connection for add order")
        return

    def ws_send(self, **kargs):
	    # Example: ./krakenws.py addOrder pair=XBT/EUR type=sell ordertype=limit price=7500 volume=0.125
        # '{"event":"addOrder", "token":"W4ytptkui/C8+zBmVQJsspQcnwMSoYil1e7/8WW1aYk", "pair":"XBT/EUR", "type":"sell", "ordertype":"limit", "price":"7500", "volume":"0.125"}'

        # symbol_pair: str, type: str, order_type: str, price: float, quantity: float

        api_data = ""

        if kargs["order_type"] == "limit":
            api_data = '{"event":"%(feed)s", "token":"%(token)s", "pair":"%(symbol_pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s", "price":"%(price)s", "volume":"%(volume)s"}' \
                % {"feed":"addOrder", "token": self.api_token, "pair":kargs["symbol_pair"], "type":kargs["type"], "ordertype":kargs["order_type"], "price":kargs["price"], "volume":kargs["quantity"]} 
                
        if kargs["order_type"] == "market":
            api_data = '{"event":"%(feed)s", "token":"%(token)s", "pair":"%(pair)s", "type":"%(type)s", "ordertype":"%(ordertype)s",  "volume":"%(volume)s"}' \
                % {"feed":"addOrder", "token": self.api_token, "pair":kargs["symbol_pair"], "type":kargs["type"], "ordertype":kargs["order_type"], "volume":kargs["quantity"]} 
        self.ws.send(api_data)
        return

    def ws_thread(self, *args) -> None:
        self.ws = WebSocketApp(
            url="wss://ws-auth.kraken.com/",
            on_open=self.ws_open,
            on_message=self.ws_message,
            on_error=self.ws_error)

        self.ws.run_forever()
        return