from pymongo.mongo_client                             import MongoClient
from pymongo.collection                               import Collection

from pprint import pprint
from bot_features.low_level.kraken_enums import *


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

    def in_safety_orders(self, symbol_pair: str) -> bool:
        return bool(self.c_safety_orders.count_documents({"_id": symbol_pair}) != 0)

    def not_in_safety_orders(self, symbol_pair: str) -> bool:
        print(self.c_safety_orders.count_documents({"_id": symbol_pair}) != 0)
        return self.c_safety_orders.count_documents({"_id": symbol_pair}) != 0

    def get_safety_order_table(self) -> dict():
        return self.c_safety_orders.find()
    
    def has_safety_order_table(self, symbol_pair):
        return False if self.c_open_symbols.count_documents({"symbol_pair": symbol_pair}) == 0 else True

    def print_so_collection(self) -> None:
        for document in self.c_safety_orders.find():
            pprint(document)
        return

    def base_order_place_sell(self, symbol_pair) -> None:
        """Change has_placed_sell_order from False to True."""
        for document in self.mdb.c_safety_orders.find({'_id': symbol_pair}):
            for value in document.values():
                if isinstance(value, dict):
                    base_order = value['base_order']
                    if base_order['has_placed_sell_order'] == False:
                        base_order['has_placed_sell_order'] = True
                        new_values = {"$set": {symbol_pair: value}}
                        query      = {'_id': symbol_pair}
                        self.c_safety_orders.find_one_and_update(query, new_values)
        return