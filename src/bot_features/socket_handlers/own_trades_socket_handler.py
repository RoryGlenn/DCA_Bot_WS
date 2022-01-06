import json

from pprint                                           import pprint
from websocket._app                                   import WebSocketApp

from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase
from bot_features.low_level.kraken_enums              import *
from bot_features.orders.base_order                   import BaseOrder
from bot_features.orders.safety_order                 import SafetyOrder

from bot_features.low_level.kraken_rest_api           import KrakenRestAPI
from bot_features.database.mongo_database             import MongoDatabase
from util.globals                                     import G
from util.config                                      import g_config


class OwnTradesSocketHandler(SocketHandlerBase):
    def __init__(self, api_token) -> None:
        self.api_token = api_token
        self.trades    = {}
        self.rest_api  = KrakenRestAPI(g_config.API_KEY, g_config.API_SECRET)
        self.mdb       = MongoDatabase()
        return

    def __finish_trade(self, s_symbol_pair: str) -> None:
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
        G.log.print_and_log(f"{s_symbol_pair} trade complete!", G.print_lock)
        return

    def ws_message(self, ws: WebSocketApp, message: str) -> None:
        message = json.loads(message)

        if isinstance(message, list):
            if isinstance(message[-1], dict):
                if 'sequence' in message[-1].keys():
                    if message[-1]['sequence'] >= 2:
                        message = message[0]
                        
                        for dictionary in message:
                            for trade_txid, trade_info in dictionary.items():
                                order_txid              = trade_info['ordertxid']
                                self.trades[order_txid] = trade_info
                                s_symbol_pair           = trade_info['pair']

                                # if its a buy, cancel the current sell order and place a new one
                                if trade_info['type'] == 'buy':
                                    if not self.mdb.is_safety_order(s_symbol_pair, order_txid):
                                        # base order was filled, no need to do anything.
                                        pass
                                    else: 
                                        # A safety order was filled!
                                        
                                        placed_safety_orders = self.mdb.get_placed_safety_order_data(s_symbol_pair)
                                        
                                        for safety_order in placed_safety_orders:
                                            if safety_order['order_txid'] == order_txid:
                                                self.mdb.update_filled_safety_order(s_symbol_pair, order_txid)
                                                filled_so_nums = self.mdb.get_filled_safety_order_numbers(s_symbol_pair)

                                                # code below figures out which safety order was filled.

                                                if filled_so_nums[-1] == 1:
                                                    # the first safety order has filled so cancel the base sell order
                                                    base_order = BaseOrder(g_config.API_KEY, g_config.API_SECRET)
                                                    base_order.cancel_sell(s_symbol_pair, filled_so_nums[-1]+1)
                                                else:
                                                    safety_order = SafetyOrder(g_config.API_KEY, g_config.API_KEY)
                                                    safety_order.cancel_sell(s_symbol_pair, filled_so_nums[-2])
                                                    safety_order.sell(s_symbol_pair, filled_so_nums[-1])
                                elif trade_info['type'] == 'sell':
                                    self.__finish_trade(s_symbol_pair)
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
        G.log.print_and_log("ownTrades: opened socket", G.print_lock)
        
        api_data = '{"event":"subscribe", "subscription":{"name":"%(feed)s", "token":"%(token)s"}}' % {"feed":"ownTrades", "token":self.api_token}
        ws.send(api_data)
        return

    def ws_close(self, ws: WebSocketApp, close_status_code: int, close_msg: str) -> None:
        G.log.print_and_log(f"ownTrades: closed socket, status code: {close_status_code}, close message:{close_msg}", G.print_lock)
        return

    def ws_error(self, ws: WebSocketApp, error_message: str) -> None:
        G.log.print_and_log(f"ownTrades: Error {str(error_message)}", G.print_lock)
        return

    def ws_thread(self, *args) -> None:
        while True:
            ws = WebSocketApp(
                url=WEBSOCKET_PRIVATE_URL,
                on_open=self.ws_open,
                on_close=self.ws_close,
                on_message=self.ws_message,
                on_error=self.ws_error)
            ws.run_forever()
        return