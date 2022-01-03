"""dca.py - DCA is a dollar cost averaging technique. 
This bot uses DCA in order lower the average buy price for a purchased coin."""

from bot_features.database.mongo_database import MongoDatabase
from bot_features.low_level.kraken_enums  import *
from util.config                          import Config


class DCA():
    def __init__(self, symbol: str, symbol_pair: str, base_order_size: float, safety_order_size: float, entry_price: float):
        super().__init__()

        self.deviation_percentage_levels:       list          = [ ]
        self.price_levels:                      list          = [ ]
        self.quantities:                        list          = [ ]
        self.total_quantities:                  list          = [ ]
        self.average_price_levels:              list          = [ ]
        self.required_price_levels:             list          = [ ]
        self.required_change_percentage_levels: list          = [ ]
        self.profit_levels:                     list          = [ ]
        self.cost_levels:                       list          = [ ]
        self.total_cost_levels:                 list          = [ ]
        self.symbol:                            str           = symbol
        self.symbol_pair:                       str           = symbol_pair
        self.entry_price:                       float         = entry_price
        self.base_order_size:                   float         = base_order_size
        self.base_target_price:                 float         = 0.0
        self.safety_order_size:                 float         = safety_order_size
        self.safety_orders:                     dict          = { }
        self.mdb:                               MongoDatabase = MongoDatabase()
        self.config:                            Config        = Config()
        return

    def start(self) -> None:
        """Essentially the main function for DCA class.

        1. If the .xlsx file associated with the symbol passed in exists, the bot has previously
        put in at least DCA_.SAFETY_ORDERS_ACTIVE_MAX orders into the exchange. 
        The bot will continue to read from the .xlsx file until it runs out of safety orders.
        
        2. Once the bot runs out of safety orders, there is nothing left to do but to wait until the
        right time to sell the coin.

        3. If the sheet doesn't exist, the bot has not traded the coin and we should create a new one if the bot trades it.
        
        """

        """
        Need a way to sell the amount of coin from all the previous orders.
        This may include the quantity that we have no bought yet but is in an open order.
        """

        

        if not self.__has_safety_order_table():
            self.__set_base_target_price()
            self.__set_deviation_percentage_levels()
            self.__set_price_levels()
            self.__set_quantity_levels()
            self.__set_total_quantity_levels()
            self.__set_weighted_average_price_levels()
            self.__set_required_price_levels()
            self.__set_required_change_percentage_levels()
            self.__set_profit_levels()
            self.__set_cost_levels()
            self.__set_total_cost_levels()
        return

    def __has_safety_order_table(self) -> bool:
        """Returns True if safety orders exists."""
        if self.mdb.c_open_symbols.count_documents({"symbol_pair": self.symbol_pair}) == 0:
            return False
        return True

    def __set_base_target_price(self) -> None:
        self.base_target_price = self.entry_price + ( self.entry_price * (self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_TARGET_PROFIT_PERCENT]/100) )
        return

    def __set_deviation_percentage_levels(self) -> None:
        """
        Safety order step scale:

        The scale will multiply step in percents between safety orders.
        Let's assume there is a bot with safety order price deviation 1% and the scale is 2. Safety order prices would be:

        It's the first order, we use deviation to place it: 0 + -1% = -1%.

        Last safety order step multiplied by the scale and then added to the last order percentage. The last step was 1%, the new step will be 1% * 2 = 2%. The order will be placed: -1% + -2% = -3%.

        Step 1: ...           Order 1: 0%  + 1%  = 1% (initial price deviation)
        Step 2: 1% * 2 = 2%.  Order 2: 1%  + 2%  = 3%.
        Step 3: 2% * 2 = 4%.  Order 3: 3%  + 4%  = 7%.
        Step 4: 4% * 2 = 8%.  Order 4: 7%  + 8%  = 15%.
        Step 5: 8% * 2 = 16%. Order 5: 15% + 16% = 31%.

        For more info: https://help.3commas.io/en/articles/3108940-main-settings
        """     
        
        # for first safety order
        self.deviation_percentage_levels.append(round(self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDER_PRICE_DEVIATION], DECIMAL_MAX))

        # for second safety order
        step_percent = self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDER_PRICE_DEVIATION] * self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDER_STEP_SCALE]
        safety_order = self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDER_PRICE_DEVIATION] + step_percent
        self.deviation_percentage_levels.append(round(safety_order, DECIMAL_MAX))
        
        # for 3rd to DCA_.SAFETY_ORDERS_MAX
        for _ in range(2, self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
            step_percent = step_percent * self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDER_STEP_SCALE]
            safety_order = safety_order + step_percent
            safety_order = round(safety_order, DECIMAL_MAX)
            self.deviation_percentage_levels.append(safety_order)
        return

    def __set_price_levels(self) -> None:
        """Save the coin prices levels in terms of USD into self.price_levels.
        Order 0: $34.4317911
        Order 1: $33.72431722
        Order n: ..."""

        # safety orders
        for i in range(self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
            level = self.deviation_percentage_levels[i] / 100
            price = self.entry_price - (self.entry_price * level)
            self.price_levels.append(round(price, DECIMAL_MAX))
        return

    def __set_quantity_levels(self) -> None:
        """Sets the quantity to buy for each safety order number."""
        # prev = self.safety_order_size
        prev = self.safety_order_size
        
        # first safety order
        self.quantities.append(self.safety_order_size)

        # remaining safety orders
        for _ in range(1, self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
            quantity = round(self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDER_VOLUME_SCALE] * prev, DECIMAL_MAX)
            self.quantities.append(quantity)
            prev = self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDER_VOLUME_SCALE] * prev
        return
    
    def __set_total_quantity_levels(self) -> None:
        """Sets the total quantity bought at each level."""
        prev = self.safety_order_size
        for i in range(self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
            sum = prev + self.quantities[i]
            sum = round(sum, DECIMAL_MAX)
            self.total_quantities.append(sum)
            prev = self.total_quantities[i]
        return
    
    
    def __set_weighted_average_price_levels(self) -> None:
        """Sets the weighted average price level for each safety order number."""
        base_order_qty = self.entry_price * self.safety_order_size
        
        for i in range(self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
            numerator = 0
            for j in range(i+1):
                numerator += self.price_levels[j] * self.quantities[j]
                
            numerator += base_order_qty
            weighted_average = numerator / self.total_quantities[i]
            weighted_average = round(weighted_average, DECIMAL_MAX)
            self.average_price_levels.append(weighted_average)
        return    
    
    def __set_required_price_levels(self) -> None:
        """Sets the required price for each safety order number."""
        target_profit_decimal = (self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_TARGET_PROFIT_PERCENT] / 100)

        # safety orders
        for i in range(self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
            required_price = self.average_price_levels[i] + (self.average_price_levels[i] * target_profit_decimal)
            required_price = round(required_price, DECIMAL_MAX)
            self.required_price_levels.append(required_price)
        return

    def __set_required_change_percentage_levels(self) -> None:
        """Sets the required change percent for each safety order number."""
        for i in range(self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
            required_change_percentage = ((self.required_price_levels[i] / self.price_levels[i]) - 1) * 100
            required_change_percentage = round(required_change_percentage, DECIMAL_MAX)
            self.required_change_percentage_levels.append(required_change_percentage)
        return
    
    def __set_profit_levels(self) -> None:
        """The more safety orders that are filled, the larger the profit will be.
        Each profit level is based on the previous profit level except for the base order."""
        
        prev = self.safety_order_size
        
        for i in range(self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
            usd_value  = self.price_levels[i] * (self.quantities[i] + prev)
            usd_profit = (self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_TARGET_PROFIT_PERCENT] / 100) * usd_value
            usd_profit = round(usd_profit, DECIMAL_MAX)
            self.profit_levels.append(usd_profit)
            prev += self.quantities[i]
        return
    
    def __set_cost_levels(self) -> None:
        """Sets the cost (USD) spent for each safety order row."""

        for i in range(self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
            cost = self.price_levels[i] * self.quantities[i]
            cost = round(cost, DECIMAL_MAX)
            self.cost_levels.append(cost)
        return
    
    def __set_total_cost_levels(self) -> None:
        """Sets the total cost (USD) for each safety order row.
        This includes the prev order costs. """

        total_cost = self.entry_price * self.safety_order_size
        
        for i in range(self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
            total_cost += self.price_levels[i] * self.quantities[i]
            total_cost = round(total_cost, DECIMAL_MAX)
            self.total_cost_levels.append(total_cost)
        return

    def store_in_db(self):
        safety_order_list = list()
        data              = {'symbol': self.symbol, 'symbol_pair': self.symbol_pair, 'base_order': {}, 'safety_orders': {}}
        value             = self.entry_price * self.base_order_size
        profit            = value * (self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_TARGET_PROFIT_PERCENT] / 100)
        profit            = round(profit, 8)

        # base order
        base_order = {
            'deviation_percentage':       0,
            'quantity':                   self.base_order_size,
            'total_quantity':             self.base_order_size,
            'price':                      self.entry_price,
            'average_price':              self.entry_price,
            'required_price':             self.entry_price + (self.entry_price * (self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_TARGET_PROFIT_PERCENT] / 100)),
            'required_change_percentage': self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_TARGET_PROFIT_PERCENT],
            'profit':                     profit,
            'cost':                       self.entry_price * self.base_order_size,
            'total_cost':                 self.entry_price * self.base_order_size,
            'has_placed_buy_order':       True,
            'has_placed_sell_order':      False,
            'has_cancelled_sell_order':   False,
            'sell_order_txid':            ''
        }

        # safety orders
        for i in range(self.config.DCA_DATA[self.symbol][ConfigKeys.DCA_SAFETY_ORDERS_MAX]):
            safety_order_list.append(
            {str(i+1):
                {
                    'deviation_percentage':       self.deviation_percentage_levels[i],
                    'quantity':                   self.quantities[i],
                    'total_quantity':             self.total_quantities[i],
                    'price':                      self.price_levels[i],
                    'average_price':              self.average_price_levels[i],
                    'required_price':             self.required_price_levels[i],
                    'required_change_percentage': self.required_change_percentage_levels[i],
                    'profit':                     self.profit_levels[i],
                    'cost':                       self.cost_levels[i],
                    'total_cost':                 self.total_cost_levels[i],
                    'has_placed_order':           False,
                    'has_filled':                 False,
                    'has_cancelled_sell_order':   False,
                    'buy_order_txid':             '',
                    'sell_order_txid':            ''
                }
            })
        
        data['base_order']    = base_order
        data['safety_orders'] = safety_order_list

        if self.mdb.c_safety_orders.count_documents({'_id': self.symbol_pair}) == 0:
            self.mdb.c_safety_orders.insert_one({'_id': self.symbol_pair, self.symbol_pair: data})
        return