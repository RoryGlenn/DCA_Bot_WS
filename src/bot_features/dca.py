"""dca.py - DCA is a dollar cost averaging technique. 
This bot uses DCA in order lower the average buy price for a purchased coin."""

# from bot_features.low_level.kraken_enums import *
# from my_sql.sql                          import SQL

from bot_features.kraken_enums import *
from bot_features.my_sql import SQL

class DCA(DCA_):
    def __init__(self, symbol_pair: str, symbol: str, order_min: float, bid_price: float):
        self.percentage_deviation_levels:       list         = [ ]
        self.price_levels:                      list         = [ ]
        self.quantities:                        list         = [ ]
        self.total_quantities:                  list         = [ ]
        self.average_price_levels:              list         = [ ]
        self.required_price_levels:             list         = [ ]
        self.required_change_percentage_levels: list         = [ ]
        self.profit_levels:                     list         = [ ]
        self.cost_levels:                       list         = [ ]
        self.total_cost_levels:                 list         = [ ]
        self.symbol:                            str          = symbol
        self.symbol_pair:                       str          = symbol_pair
        self.bid_price:                         float        = bid_price
        self.order_min:                         float        = order_min
        self.safety_orders:                     dict         = { }
        self.__start()

    def __start(self) -> None:
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
            self.__set_safety_order_table()
        
        self.__set_buy_orders()
        return

    def __has_safety_order_table(self) -> bool:
        """Returns True if safety orders exists."""
        sql = SQL()
        result_set = sql.con_query(f"SELECT * FROM safety_orders WHERE symbol_pair='{self.symbol_pair}'")

        if result_set.rowcount <= 0:
            return False

        return not len(result_set.fetchall()) <= 0

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
        self.percentage_deviation_levels.append(round(DCA_.SAFETY_ORDER_PRICE_DEVIATION, DECIMAL_MAX))

        # for second safety order
        step_percent = DCA_.SAFETY_ORDER_PRICE_DEVIATION * DCA_.SAFETY_ORDER_STEP_SCALE
        safety_order = DCA_.SAFETY_ORDER_PRICE_DEVIATION + step_percent
        self.percentage_deviation_levels.append(round(safety_order, DECIMAL_MAX))
        
        # for 3rd to DCA_.SAFETY_ORDERS_MAX
        for _ in range(2, DCA_.SAFETY_ORDERS_MAX):
            step_percent = step_percent * DCA_.SAFETY_ORDER_STEP_SCALE
            safety_order = safety_order + step_percent
            safety_order = round(safety_order, DECIMAL_MAX)
            self.percentage_deviation_levels.append(safety_order)
        return

    def __set_price_levels(self) -> None:
        """Save the coin prices levels in terms of USD into self.price_levels.
        Order 0: $34.4317911
        Order 1: $33.72431722
        Order n: ..."""

        # safety orders
        for i in range(DCA_.SAFETY_ORDERS_MAX):
            level = self.percentage_deviation_levels[i] / 100
            price = self.bid_price - (self.bid_price * level)
            self.price_levels.append(round(price, DECIMAL_MAX))
        return

    def __set_quantity_levels(self) -> None:
        """Sets the quantity to buy for each safety order number."""
        prev = self.order_min
        
        # first safety order
        self.quantities.append(self.order_min)

        # remaining safety orders
        for _ in range(1, DCA_.SAFETY_ORDERS_MAX):
            self.quantities.append(DCA_.SAFETY_ORDER_VOLUME_SCALE * prev)
            prev = DCA_.SAFETY_ORDER_VOLUME_SCALE * prev
        return
    
    def __set_total_quantity_levels(self) -> None:
        """Sets the total quantity bought at each level."""
        prev = self.order_min
        for i in range(DCA_.SAFETY_ORDERS_MAX):
            sum = prev + self.quantities[i]
            self.total_quantities.append(sum)
            prev = self.total_quantities[i]
        return
    
    
    def __set_weighted_average_price_levels(self) -> None:
        """Sets the weighted average price level for each safety order number."""
        base_order_qty = self.bid_price * self.order_min
        
        for i in range(DCA_.SAFETY_ORDERS_MAX):
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
        target_profit_decimal = DCA_.TARGET_PROFIT_PERCENT / 100

        # safety orders
        for i in range(DCA_.SAFETY_ORDERS_MAX):
            required_price = self.average_price_levels[i] + (self.average_price_levels[i] * target_profit_decimal)
            required_price = round(required_price, DECIMAL_MAX)
            self.required_price_levels.append(required_price)
        return

    def __set_required_change_percentage_levels(self) -> None:
        """Sets the required change percent for each safety order number."""
        
        for i in range(DCA_.SAFETY_ORDERS_MAX):
            required_change_percentage = ((self.required_price_levels[i] / self.price_levels[i]) - 1) * 100
            required_change_percentage = round(required_change_percentage, DECIMAL_MAX)
            self.required_change_percentage_levels.append(required_change_percentage)
        return
    
    def __set_profit_levels(self) -> None:
        """The more safety orders that are filled, the larger the profit will be.
        Each profit level is based on the previous profit level except for the base order."""
        
        prev = self.order_min
        
        for i in range(DCA_.SAFETY_ORDERS_MAX):
            usd_value  = self.price_levels[i] * (self.quantities[i] + prev)
            usd_profit = (DCA_.TARGET_PROFIT_PERCENT/100) * usd_value
            self.profit_levels.append(usd_profit)
            prev += self.quantities[i]
        return
    
    def __set_cost_levels(self) -> None:
        """Sets the cost (USD) spent for each safety order row."""

        for i in range(DCA_.SAFETY_ORDERS_MAX):
            cost = self.price_levels[i] * self.quantities[i]
            cost = round(cost, DECIMAL_MAX)
            self.cost_levels.append(cost)
        return
    
    def __set_total_cost_levels(self) -> None:
        """Sets the total cost (USD) for each safety order row.
        This includes the prev order costs. """

        total_cost = self.bid_price * self.order_min
        
        for i in range(DCA_.SAFETY_ORDERS_MAX):
            total_cost += self.price_levels[i] * self.quantities[i]
            total_cost = round(total_cost, DECIMAL_MAX)
            self.total_cost_levels.append(total_cost)
        return

    def __set_safety_order_table(self) -> None:
        """Set the Dataframe with the values calculated in previous functions."""
        order_numbers = [i for i in range(1, DCA_.SAFETY_ORDERS_MAX+1)]

        sql = SQL()
        
        for i in range(DCA_.SAFETY_ORDERS_MAX):
            sql.con_update(f"""INSERT INTO safety_orders {sql.so_columns} VALUES (
               '{self.symbol_pair}', 
               '{self.symbol}', 
                {order_numbers[i]}, 
                {self.percentage_deviation_levels[i]},
                {self.quantities[i]},
                {self.total_quantities[i]},
                {self.price_levels[i]},
                {self.average_price_levels[i]}, 
                {self.required_price_levels[i]}, 
                {self.required_change_percentage_levels[i]},
                {self.profit_levels[i]},
                {self.cost_levels[i]},
                {self.total_cost_levels[i]},
                false,
                so_no)""")
        return
    
    def __set_buy_orders(self) -> None:
        """Read rows in the .xlsx file into memory."""
        sql = SQL()

        quantities = sql.con_get_quantities(self.symbol_pair)
        prices     = sql.con_get_prices(self.symbol_pair)
        iterations = len(prices) if len(prices) < DCA_.SAFETY_ORDERS_ACTIVE_MAX else DCA_.SAFETY_ORDERS_ACTIVE_MAX

        for i in range(iterations):
            self.safety_orders[prices[i]] = quantities[i]
        return
