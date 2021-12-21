import pymongo
from bot_features.low_level.kraken_enums import *

class MongoDatabase():
    def __init__(self) -> None:
        self.db             = pymongo.MongoClient()[DB.DATABASE_NAME]
        self.c_open_symbols = self.db[DB.COLLECTION_OS]
        self.c_add_order    = self.db[DB.COLLECTION_AO]
        self.c_balances     = self.db[DB.COLLECTION_B]
        self.c_own_trades   = self.db[DB.COLLECTION_OT]
        self.c_open_orders  = self.db[DB.COLLECTION_OO]
        self.c_safety_orders = self.db[DB.COLLECTION_SO]
        return


    def insert(self):

        """

        XBTUSD: {
                    symbol: XBT
                    symbol_pair: XBTUSD
                    
                    base_order: {
                                percentage_deviation_level:       0,
                                quantity:                         base_order_size,
                                total_quantity:                   base_order_size,
                                price_level:                      entry_price,
                                average_price_level:              entry_price,
                                required_price_level:             entry_price + (entry_price*target_profit_percent),
                                required_change_percentage_level: target_profit_percent,
                                profit_level:                     profit,
                                cost_level:                       cost,
                                total_cost_levels:                cost,
                                order_placed:                     False
                    },

                    safety_orders: {

                        1:
                            {
                                percentage_deviation_level:       percentage_deviation_levels[i],
                                quantity:                         quantities[i],
                                total_quantity:                   total_quantities[i],
                                price_level:                      price_levels[i],
                                average_price_level:              average_price_levels[i], 
                                required_price_level:             required_price_levels[i], 
                                required_change_percentage_level: required_change_percentage_levels[i],
                                profit_level:                     profit_levels[i],
                                cost_level:                       cost_levels[i],
                                total_cost_levels:                total_cost_levels[i],
                                order_placed:                     False
                            }
                        2:
                            {
                                percentage_deviation_level:       percentage_deviation_levels[i],
                                quantity:                         quantities[i],
                                total_quantity:                   total_quantities[i],
                                price_level:                      price_levels[i],
                                average_price_level:              average_price_levels[i], 
                                required_price_level:             required_price_levels[i], 
                                required_change_percentage_level: required_change_percentage_levels[i],
                                profit_level:                     profit_levels[i],
                                cost_level:                       cost_levels[i],
                                total_cost_levels:                total_cost_levels[i],
                                order_placed:                     False
                            }
                        
                        3:
                            {
                                percentage_deviation_level:       percentage_deviation_levels[i],
                                quantity:                         quantities[i],
                                total_quantity:                   total_quantities[i],
                                price_level:                      price_levels[i],
                                average_price_level:              average_price_levels[i], 
                                required_price_level:             required_price_levels[i], 
                                required_change_percentage_level: required_change_percentage_levels[i],
                                profit_level:                     profit_levels[i],
                                cost_level:                       cost_levels[i],
                                total_cost_levels:                total_cost_levels[i],
                                order_placed:                     False
                            }

                    }
                    
                }
    
        """
        

        return



    def get_safety_order_table(self):
        
        return

    
    def has_safety_order_table(self, symbol_pair):
        return False if self.c_open_symbols.count_documents({"symbol_pair": symbol_pair}) == 0 else True




    