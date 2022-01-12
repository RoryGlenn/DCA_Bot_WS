import json

from pprint                                           import pprint
from websocket._app                                   import WebSocketApp

from bot_features.socket_handlers.socket_handler_base import SocketHandlerBase

from bot_features.orders.base_order                   import BaseOrder
from bot_features.orders.safety_order                 import SafetyOrder

from bot_features.low_level.kraken_enums              import *
from bot_features.low_level.kraken_rest_api           import KrakenRestAPI

from bot_features.database.mongo_database             import MongoDatabase

from util.colors                                      import Color
from util.globals                                     import G
from util.config                                      import g_config


class OwnTradesSocketHandler(SocketHandlerBase):
    def __init__(self, api_token: str) -> None:
        self.api_token    = api_token
        self.trades       = dict()
        self.rest_api     = KrakenRestAPI(g_config.API_KEY, g_config.API_SECRET)
        self.mdb          = MongoDatabase()
        self.base_order   = BaseOrder(g_config.API_KEY, g_config.API_SECRET)
        self.safety_order = SafetyOrder(g_config.API_KEY, g_config.API_SECRET)
        return

    def __get_profit(self, s_symbol_pair: str, placed_safety_orders: list) -> float:
        for i in range(len(placed_safety_orders)):
            if placed_safety_orders[i]['sell_order_txid'] == '':
                # the previous one completed
                if i == 0:
                    # base sell
                    return self.mdb.get_base_order_profit(s_symbol_pair)
                else:
                    # safety order
                    return float(placed_safety_orders[i-1]['profit'])
        return -1

    def __finish_trade(self, s_symbol_pair: str) -> None:
        # if its a sell, cancel all orders associated with the symbol and wipe the db
        if self.mdb.in_safety_orders(s_symbol_pair):
            placed_safety_orders = self.mdb.get_placed_safety_order_data(s_symbol_pair)
            profit               = self.__get_profit(s_symbol_pair, placed_safety_orders)

            # cancel all orders associated with the symbol
            for safety_order in placed_safety_orders:
                self.rest_api.cancel_order(safety_order['buy_order_txid'])

            # remove all data associated with s_symbol_pair from db
            self.mdb.c_safety_orders.delete_one({"_id": s_symbol_pair})

            # profit = exit_cost - entry_cost - maker_fee - taker_fee
            G.log.print_and_log(Color.BG_GREEN + f"{s_symbol_pair} trade complete{Color.ENDC}, profit: ${profit}", G.print_lock)

            # add back to available usd?????????????????????????????????????
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
                                        
                                        G.log.print_and_log(f"A safety order was filled: {s_symbol_pair} {order_txid}", G.print_lock)
                                        
                                        placed_safety_orders = self.mdb.get_placed_safety_order_data(s_symbol_pair)
                                        
                                        for safety_order in placed_safety_orders:
                                            if safety_order['buy_order_txid'] == order_txid:
                                                self.mdb.update_filled_safety_order(s_symbol_pair, order_txid)
                                                filled_so_nums = self.mdb.get_filled_safety_order_numbers(s_symbol_pair)

                                                # code below figures out which safety order was filled.
                                                if len(filled_so_nums) > 0:
                                                    if filled_so_nums[-1] == '1':
                                                        # the first safety order has filled so cancel the base sell order
                                                        self.base_order.cancel_sell(s_symbol_pair)
                                                        self.safety_order.sell(s_symbol_pair, '1')
                                                    else:
                                                        # a safety order higher than 1 was filled.
                                                        so_cancel_num_str = str( int(filled_so_nums[-2]) + 1 )
                                                        G.log.print_and_log(f"so_cancel_num_str: {so_cancel_num_str}", G.print_lock)

                                                        self.safety_order.cancel_sell(s_symbol_pair, so_cancel_num_str)
                                                        G.log.print_and_log(f"s_symbol_pair: {s_symbol_pair}, filled_so_nums[-1]: {filled_so_nums[-1]}", G.print_lock)

                                                        self.safety_order.sell(s_symbol_pair, filled_so_nums[-1])
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
