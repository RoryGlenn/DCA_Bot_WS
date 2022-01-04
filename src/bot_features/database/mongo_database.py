from pymongo.mongo_client                             import MongoClient
from pymongo.collection                               import Collection
from pprint                                           import pprint
from bot_features.low_level.kraken_enums              import *


class MongoDatabase():
    def __init__(self) -> None:
        self.mdb:             MongoClient = MongoClient()[DB.DATABASE_NAME]
        self.c_open_symbols:  Collection  = self.mdb[DB.COLLECTION_OS]
        self.c_add_order:     Collection  = self.mdb[DB.COLLECTION_AO]
        self.c_balances:      Collection  = self.mdb[DB.COLLECTION_B]
        self.c_own_trades:    Collection  = self.mdb[DB.COLLECTION_OT]
        self.c_open_orders:   Collection  = self.mdb[DB.COLLECTION_OO]
        self.c_safety_orders: Collection  = self.mdb[DB.COLLECTION_SO]
        return



    def print_so_collection(self) -> None:
        for document in self.c_safety_orders.find():
            pprint(document)
        return


####################
### BASE ORDER
####################

    def base_order_place_sell(self, symbol_pair: str, sell_order_txid: str) -> None:
        """Change has_placed_sell_order from False to True."""
        for document in self.c_safety_orders.find({'_id': symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    base_order = value['base_order']
                    if base_order['has_placed_sell_order'] == False:
                        base_order['has_placed_sell_order'] = True
                        base_order['sell_order_txid'] = sell_order_txid
                        new_values = {"$set": {symbol_pair: value}}
                        query      = {'_id': symbol_pair}
                        self.c_safety_orders.find_one_and_update(query, new_values)
        return

    def get_base_order_sell_txid(self, s_symbol_pair: str) -> str:
        for document in self.c_safety_orders.find({'_id': s_symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    base_order = value['base_order']
                    return base_order['sell_order_txid']
        raise Exception("Can't find base order txid!")



####################
### SAFETY ORDERS
####################
    def get_safety_order_table(self) -> dict():
        return self.c_safety_orders.find()
    
    def has_safety_order_table(self, symbol_pair: str):
        return False if self.c_open_symbols.count_documents({"symbol_pair": symbol_pair}) == 0 else True

    def in_safety_orders(self, symbol_pair: str) -> bool:
        return bool(self.c_safety_orders.count_documents({"_id": symbol_pair}) != 0)

    def is_safety_order(self, s_symbol_pair: str, order_txid: str) -> bool:
        for document in self.c_safety_orders.find({'_id': s_symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    for safety_order in value['safety_orders']:
                        for so_data in safety_order.values():
                            if so_data['buy_order_txid'] == order_txid:
                                return True
        return False

    def get_number_of_open_safety_orders(self, symbol_pair: str) -> int:
        count = 0
        
        for document in self.c_safety_orders.find({'_id': symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    safety_orders = value['safety_orders']
                    for safety_order in safety_orders:
                        for so_data in safety_order.values():
                            if so_data['has_placed_order'] and not so_data['has_filled']: 
                                # if the order has been placed but has not been filled, it must be open!
                                count += 1
        return count

    def get_unplaced_safety_order_data(self, s_symbol_pair: str) -> list:
        unplaced_list = []
        for document in self.c_safety_orders.find({'_id': s_symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    for safety_order in value['safety_orders']:
                        for _, so_data in safety_order.items():
                            if not so_data['has_placed_order'] and not so_data['has_filled']:
                                unplaced_list.append(so_data)
        return unplaced_list

    def get_placed_safety_order_data(self, s_symbol_pair: str) -> list:
        unplaced_list = []
        for document in self.c_safety_orders.find({'_id': s_symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    for safety_order in value['safety_orders']:
                        for _, so_data in safety_order.items():
                            if so_data['has_placed_order'] and not so_data['has_filled']:
                                unplaced_list.append(so_data)
        return unplaced_list


    def get_filled_safety_order_numbers(self, s_symbol_pair: str) -> list:
        filled_list = []
        for document in self.c_safety_orders.find({'_id': s_symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    for safety_order in value['safety_orders']:
                        for so_num, so_data in safety_order.items():
                            if so_data['has_placed_order'] and so_data['has_filled']:
                                filled_list.append(so_num)
        return filled_list



    def get_unplaced_safety_order_numbers(self, s_symbol_pair: str) -> list:
        so_numbers = []
        for document in self.c_safety_orders.find({'_id': s_symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    for safety_order in value['safety_orders']:
                        for so_num, so_data in safety_order.items():
                            if not so_data['has_placed_order'] and not so_data['has_filled']:
                                so_numbers.append(so_num)
        return so_numbers
    
    def update_filled_safety_order(self, s_symbol_pair: str, order_txid: str) -> None:
        """change the safety order associated with s_symbol and order_txid to: has_filled = True"""
        for document in self.c_safety_orders.find({'_id': s_symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    for safety_order in value['safety_orders']:
                        for so_data in safety_order.values():
                            if so_data['order_txid'] == order_txid:
                                so_data['has_filled'] = True
                                new_values = {"$set": {s_symbol_pair: value}}
                                query      = {'_id': s_symbol_pair}
                                self.c_safety_orders.find_one_and_update(query, new_values)
        return

    def update_placed_safety_order(self, s_symbol_pair: str, safety_order_num: int, buy_order_txid: str) -> None:
        """Set so_data['has_placed_order'] = True"""
        for document in self.c_safety_orders.find({'_id': s_symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    for safety_order in value['safety_orders']:
                        for so_num, so_data in safety_order.items():
                            if so_num == safety_order_num:
                                if so_data['buy_order_txid'] == buy_order_txid:
                                    so_data['has_placed_order'] = True
                                    new_values                  = {"$set": {s_symbol_pair: value}}
                                    query                       = {'_id': s_symbol_pair}
                                    self.c_safety_orders.find_one_and_update(query, new_values)
        return

    def cancel_safety_sell_order(self, s_symbol_pair: str, order_txid: str) -> None:
        return
    
    def store_safety_order_buy_txid(self, s_symbol_pair: str, safety_order_num: int, buy_order_txid: str) -> None:
        for document in self.c_safety_orders.find({'_id': s_symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    for safety_order in value['safety_orders']:
                        for so_num, so_data in safety_order.items():
                            if so_num == safety_order_num:
                                so_data['buy_order_txid'] = buy_order_txid
                                new_values                = {"$set": {s_symbol_pair: value}}
                                query                     = {'_id': s_symbol_pair}
                                self.c_safety_orders.find_one_and_update(query, new_values)
        return



##########################################################

    def get_value(self, s_symbol_pair: str, order_txid: str) -> float:
        for document in self.c_safety_orders.find({'_id': s_symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    for safety_order in value['safety_orders']:
                        for so_data in safety_order.values():
                            if so_data['buy_order_txid'] == order_txid:
                                price = so_data['price']
                                quantity = so_data['quantity']
                                return round(price * quantity, DECIMAL_MAX)
        return 0.0


