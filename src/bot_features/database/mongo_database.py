import pymongo

from pprint import pprint
from bot_features.low_level.kraken_enums import *
from pymongo.mongo_client                             import MongoClient
from pymongo.collection                               import Collection


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


    def in_safety_orders(self, symbol_pair: str) -> None:
        return not self.c_safety_orders.count_documents({"_id": symbol_pair}) == 0

    def get_safety_order_table(self) -> dict():
        return self.c_safety_orders.find()
    
    def has_safety_order_table(self, symbol_pair):
        return False if self.c_open_symbols.count_documents({"symbol_pair": symbol_pair}) == 0 else True

    def print_collection(self, collection: str) -> None:
        for document in collection.find():
            pprint(document)
        return

    def get_collection(self, collection: Collection) -> dict():
        return collection.find()