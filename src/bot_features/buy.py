
"""
    buy.py - Buys coin on kraken exchange based on users config file.
        1. Have a list of coins that you want to buy.
        2. Pull data from trading view based on 3c settings.
        3. Make decision on whether to buy or not.
        4. After base order is filled, create sell limit order at % higher
        5. every time a safety order is filled, cancel current sell limit order and create a new sell limit order

"""

import datetime
import time

from pprint                                 import pprint
from bot_features.kraken_enums    import *
from bot_features.kraken_bot_base import KrakenBotBase
from util.globals                           import G
from util.colors                            import Color
from bot_features.dca                       import DCA
from bot_features.sell                      import Sell
from bot_features.tradingview               import TradingView
from bot_features.my_sql                    import SQL


class Buy():
    def __init__(self) -> None:
        self.dca:          DCA   = None
        # self.sell:         Sell  = Sell(parameter_dict)
        self.total_profit: float = 0.0
        self.obo_txid:     str   = ""
        return

    def __init_loop_variables(self) -> None:
        """Initialize variables for the buy_loop."""
        self.kraken_assets_dict = self.get_asset_info()[Dicts.RESULT]
        self.account_balance    = self.get_parsed_account_balance()
        self.asset_pairs_dict   = self.get_all_tradable_asset_pairs()[Dicts.RESULT]
        
        G.log.print_and_log(message=Color.BG_GREEN + "Account Value          " + Color.ENDC + f" ${self.__get_account_value()}")
        return

    def __get_buy_time(self) -> str:
        """Returns the next time to buy as specified in the config file."""
        return ( datetime.timedelta(minutes=Buy_.TIME_MINUTES) + datetime.datetime.now() ).strftime("%H:%M:%S")

    def __place_base_order(self, order_min: float, symbol_pair: str) -> dict:
        """
            Place the base order for the coin we want to trade.
            The base order should be a market order only!
        
        """
        return self.market_order(Trade.BUY, order_min, symbol_pair)
    
    
    def __has_order_filled(self, symbol_pair: str) -> bool:
        """Check if the order has filled."""
        try:
            sql                       = SQL()
            filled_trades_order_txids = dict()
            
            result_set = sql.con_query(f"SELECT symbol_pair FROM safety_orders WHERE symbol_pair='{symbol_pair}'")

            # if symbol is not being traded, then nothing has been filled
            if result_set.rowcount <= 0:
                return False
            
            self.wait(timeout=Nap.NORMAL)
            trade_history = self.get_trades_history()
            
            if not self.has_result(trade_history):
                G.log.print_and_log("Can't get trade history")
                self.wait(timeout=10)
                raise Exception("Can't get trade history")
            
            self.wait(timeout=Nap.NORMAL)
            # get all open_buy_orders from the database to check whether the have been filled
            result_set = sql.con_query(f"SELECT obo_txid FROM open_buy_orders WHERE filled=false AND symbol_pair='{symbol_pair}'")
            
            # if there is nothing to get, nothing has been filled
            if result_set.rowcount <= 0:
                return False
            
            obo_txid_set              = {txid[0] for txid in result_set.fetchall()}
            trade_history             = trade_history[Dicts.RESULT][Data.TRADES]
            filled_trades_order_txids = {dictionary[Data.ORDER_TXID]: trade_txid for (trade_txid, dictionary) in trade_history.items()}
            
            for obo_txid in obo_txid_set:
                if obo_txid in filled_trades_order_txids.keys():
                    # open buy order has been filled!
                    self.obo_txid = obo_txid # turn self.obo_txid into a list and append each filled trade?
                    return True
        except Exception as e:
            G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
        return False
                
    def __has_completed(self, symbol_pair: str) -> bool:
            sql = SQL()
            filled_trades_order_txids = dict()

            try:
                result_set = sql.con_query(f"SELECT symbol_pair FROM safety_orders WHERE symbol_pair='{symbol_pair}'")
                
                # if symbol is not in sql db, there is nothing to do.
                if result_set.rowcount <= 0:
                    return False
                
                bought_set = {symbol[0] for symbol in result_set.fetchall()}
                
                if symbol_pair not in bought_set:
                    return False
                
                self.wait(timeout=Nap.NORMAL)
                trade_history = self.get_trades_history()
                
                if not self.has_result(trade_history):
                    G.log.print_and_log("Can't get trade history")
                    self.wait(timeout=10)
                    raise Exception("Can't get trade history")
                
                result_set = sql.con_query(f"SELECT oso_txid FROM open_sell_orders WHERE symbol_pair='{symbol_pair}' AND filled=false")
                if result_set.rowcount <= 0:
                    return False
                
                oso_txids = {txid[0] for txid in result_set.fetchall()}
                
                trade_history = trade_history[Dicts.RESULT][Data.TRADES]
                for trade_txid, dictionary in trade_history.items():
                    filled_trades_order_txids[dictionary[Data.ORDER_TXID]] = trade_txid
                
                filled_trades_order_txids = {dictionary[Data.ORDER_TXID]: trade_txid for (trade_txid, dictionary) in trade_history.items()}

                for oso_txid in oso_txids:
                    if oso_txid in filled_trades_order_txids.keys():
                        return True
            except Exception as e:
                G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
            return False
        
    def __place_safety_orders(self, symbol_pair: str) -> None:
        """Place safety orders."""
        
        sql = SQL()
        self.wait(timeout=Nap.NORMAL)
        
        for price, quantity in self.dca.safety_orders.items():
            try:
                price_max_prec      = self.get_pair_decimals(symbol_pair)
                rounded_price       = self.round_decimals_down(price, price_max_prec)
                max_vol_prec        = self.get_max_volume_precision(symbol_pair)
                rounded_quantity    = self.round_decimals_down(quantity, max_vol_prec)
                limit_order_result  = self.limit_order(Trade.BUY, rounded_quantity, symbol_pair, rounded_price)

                if self.has_result(limit_order_result):
                    result_set          = sql.con_query(f"SELECT MIN(safety_order_no) FROM safety_orders WHERE symbol_pair='{symbol_pair}' AND order_placed=false")
                    safety_order_number = sql.parse_so_number(result_set)
                    
                    G.log.print_and_log(message=Color.BG_BLUE + f"Safety order {safety_order_number} placed  {Color.ENDC} {symbol_pair} {limit_order_result[Dicts.RESULT][Dicts.DESCR][Dicts.ORDER]}", money=True)
                    obo_txid            = limit_order_result[Dicts.RESULT][Data.TXID][0]
                    
                    # change order_placed to true in safety_orders table
                    sql.con_update(f"UPDATE safety_orders SET order_placed=true WHERE symbol_pair='{symbol_pair}' AND order_placed=false LIMIT 1")
                    
                    row = sql.con_get_row(SQLTable.SAFETY_ORDERS, symbol_pair, safety_order_number)
                    
                    # store open_buy_order row
                    sql.con_update(f"""INSERT INTO open_buy_orders {sql.obo_columns} VALUES
                                   ('{row[0]}', '{row[1]}',  {row[2]},    {row[3]},
                                     {row[4]},   {row[5]},   {row[6]},    {row[7]},
                                     {row[8]},   {row[9]},   {row[10]},   {row[11]},
                                     {row[12]},  false,     '{obo_txid}', {row[14]})
                                    """)
                else:
                    if limit_order_result[Dicts.ERROR][0] == KError.INSUFFICIENT_FUNDS:
                        G.log.print_and_log(Color.FG_YELLOW + f"Not enough USD to place remaining safety orders{Color.ENDC}: {symbol_pair}")
                        return
                    elif limit_order_result[Dicts.ERROR][0] == KError.INVALID_VOLUME:
                        G.log.print_and_log(f"{symbol_pair} volume error.")
                    
                    G.log.print_and_log(message=f"{limit_order_result}", money=True)
            except Exception as e:
                G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
        
        return

    def __place_limit_orders(self, symbol: str, symbol_pair: str) -> None:
        """
            The Base order will be a market order but all the safety orders will be a limit order.
            Place the safety orders that were set inside of the DCA class.
            If the limit order was entered successfully, update the excel sheet by removing the order we just placed.

            The next sell limit order should always be from the top of the safety orders,
                For example:
                    Base order = 1,   $100
                    SO1        = 1,   $98.7
                    SO2        = 2.5, $96.5

                    Then our first sell order should be 1, for $100 + 0.5%
                    If SO1, is filled, the previous sell order should be cancelled and a new sell order should be placed: Base Order+SO1, required_price1
                    If SO2, is filled, the previous sell order should be cancelled and a new sell order should be placed: Base Order+SO1+SO2, required_price2
        """
        self.wait(timeout=Nap.NORMAL)
        sql = SQL()
        
        try:
            if symbol_pair in sql.con_get_symbol_pairs():
                # If the symbol is in the database then we have bought it before
                self.dca = DCA(symbol_pair, symbol, 0, 0)
            else:
                base_order_qty = self.get_order_min(symbol_pair)
                
                # If symbol_pair exists in database then the base order has already been placed!
                base_order_result = self.__place_base_order(base_order_qty, symbol_pair)

                if self.has_result(base_order_result):
                    base_order_price = self.__get_bought_price(base_order_result)
                    
                    G.log.print_and_log(Color.BG_BLUE + f"Base order filled      {Color.ENDC} {base_order_result[Dicts.RESULT][Dicts.DESCR][Dicts.ORDER]} {base_order_price}")
                    
                    base_order_req_price = base_order_price + (base_order_price * DCA_.TARGET_PROFIT_PERCENT/100)
                    base_order_profit    = base_order_price * base_order_qty * (DCA_.TARGET_PROFIT_PERCENT/100)
                    base_order_cost      = base_order_price * base_order_qty
                    base_order_txid      = base_order_result[Dicts.RESULT][Data.TXID][0]
                    base_order_row       = BaseOrderRow(symbol_pair, symbol, 0, DCA_.TARGET_PROFIT_PERCENT, base_order_qty, base_order_qty, base_order_price, base_order_price, base_order_req_price, DCA_.TARGET_PROFIT_PERCENT, base_order_profit, base_order_cost, base_order_cost, False, False, base_order_txid, 0)
                    
                    self.dca       = DCA(symbol_pair, symbol, base_order_qty, base_order_price)
                    self.sell.dca  = self.dca
                    
                    # upon placing the base_order, pass in the txid into dca to write to db
                    self.sell.place_sell_limit_base_order(base_order_row)
                else:
                    if base_order_result[Dicts.ERROR][0] == KError.INSUFFICIENT_FUNDS:
                        G.log.print_and_log(Color.FG_YELLOW + f"Not enough USD to place base order:{Color.ENDC} {symbol_pair}")
                    else:
                        G.log.print_and_log(Color.FG_YELLOW + f"Can't place base order:{Color.ENDC} {symbol_pair} {base_order_result[Dicts.ERROR]}")
                    return
            
            num_open_orders = sql.con_get_open_buy_orders(symbol_pair)
            
            # if the max active orders are already put in, and are still active, there is nothing left to do.
            if num_open_orders < DCA_.SAFETY_ORDERS_ACTIVE_MAX:
                self.__place_safety_orders(symbol_pair)
        except Exception as e:
            G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
        return

    def __update_completed_trades(self, symbol_pair: str) -> None:
        """
            If the sell order has been filled, we have sold the coin for a profit.
            The things left to do is:
                1. cancel remaining buy orders
                2. delete the symbol data from the tables
                4. start the process all over again!
                
        """
        try:
            sql = SQL()
                    
            if self.__has_completed(symbol_pair):
                result_set      = sql.con_query(f"SELECT profit FROM open_sell_orders WHERE symbol_pair='{symbol_pair}' AND filled=false")        
                profit          = result_set.fetchall()[0] if result_set.rowcount > 0 else 0
                profit          = profit[0][0] if isinstance(profit[0], tuple) else profit[0]
                
                G.log.print_and_log(message=Color.BG_GREEN + f"Trade complete $$$     {Color.ENDC} {symbol_pair}, profit: {profit}", money=True)
                self.total_profit += float(profit)

                result_set      = sql.con_query(f"SELECT obo_txid FROM open_buy_orders WHERE symbol_pair='{symbol_pair}' AND filled=false")
                open_buy_orders = result_set.fetchall() if result_set.rowcount > 0 else []
                
                for txid in open_buy_orders:
                    if isinstance(txid, str):
                        self.cancel_order(txid)
                    elif isinstance(txid, tuple):
                        self.cancel_order(txid[0])
                    
                # remove rows associated with symbol_pair from all tables
                sql.con_update(f"DELETE FROM safety_orders    WHERE symbol_pair='{symbol_pair}'")
                sql.con_update(f"DELETE FROM open_buy_orders  WHERE symbol_pair='{symbol_pair}'")
                sql.con_update(f"DELETE FROM open_sell_orders WHERE symbol_pair='{symbol_pair}'")
        except Exception as e:
            G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
        return

    def __update_open_buy_orders(self, symbol_pair: str) -> None:
        """
            Updates the open_buy_orders sheet if a buy limit order has been filled.
            Accomplishes this by checking to see if the txid exists in the trade history list.

            1. Read all txids from txids.xlsx file into DataFrame.
            2. For every txid in the dataframe, check if the associated order has been filled.
            3. If the limit buy order has been filled, update the AVERAGE_PRICES_FILE with the new average and new quantity.
            
            Note: Function is called only once inside of the buy loop.
            
        """
        try:
            sql = SQL()
                    
            if self.__has_order_filled(symbol_pair):
                sql.con_update(f"UPDATE open_buy_orders SET filled=true WHERE obo_txid='{self.obo_txid}' AND filled=false AND symbol_pair='{symbol_pair}'")
                row = sql.con_query(f"SELECT * FROM {SQLTable.OPEN_BUY_ORDERS} WHERE symbol_pair='{symbol_pair}' AND obo_txid='{self.obo_txid}'")

                if row.rowcount > 0:
                    row = row.fetchall()[0]
                    G.log.print_and_log(Color.BG_MAGENTA + f"""Safety order {row[2]} filled  {Color.ENDC} {row[0]}""")

                    # if the txid is in the trade history, the order open_buy_order was filled.
                    self.sell.start(symbol_pair, self.obo_txid)
        except Exception as e:
            G.log.print_and_log(e=e, error_type=type(e).__name__, filename=__file__, tb_lineno=e.__traceback__.tb_lineno)
        return
    
    def __get_account_value(self) -> float:
        """Get account value by adding all coin quantities together and putting in USD terms."""
        total   = 0.0
        account = self.get_account_balance()
        x_list  = ['XETC', 'XETH', 'XLTC', 'XMLN', 'XREP', 'XXBT', 'XXDG', 'XXLM', 'XXMR', 'XXRP', 'XZEC']

        if self.has_result(account):
            for symbol, quantity in account[Dicts.RESULT].items():
                quantity = float(quantity)
                if float(quantity) > 0:
                    if symbol[-2:] == ".S": # coin is staked
                        symbol = symbol[:-2]
                    if symbol in x_list:
                        symbol = symbol[1:]
                    if symbol == StableCoins.ZUSD or symbol == StableCoins.USD or symbol == StableCoins.USDT:
                        total += quantity
                    else:
                        bid_price = self.get_bid_price(symbol+StableCoins.USD)
                        value = bid_price * quantity
                        total += value
        return round(total, 2)

    def __get_bought_price(self, buy_result: dict) -> float:
        """Parses the buy_result to get the entry_price or bought_price of the base order."""
        bought_price = 0
        order_result = None
        
        if self.has_result(buy_result):
            
            self.wait(timeout=Nap.NORMAL)
            order_result = self.query_orders_info(buy_result[Dicts.RESULT][Data.TXID][0])
            if self.has_result(order_result):
                for txid in order_result[Dicts.RESULT]:
                    for key, value in order_result[Dicts.RESULT][txid].items():
                        if key == Data.PRICE:
                            bought_price = float(value)
                            break
        return bought_price

    def __is_buy(self, symbol: str) -> bool:
        """
            Prepare the symbol in order to pull data from TradingView
            
        """
        self.wait(timeout=Nap.NORMAL)
        alt_name = self.get_alt_name(symbol)
        return self._is_buy(alt_name+StableCoins.USD)

    #----------------------------------------------------------------------------------------------------
    # def __sell_all_assets(self) -> None:
    #     self.kraken_assets_dict = self.get_asset_info()[Dicts.RESULT]
    #     self.asset_pairs_dict   = self.get_all_tradable_asset_pairs()[Dicts.RESULT]
    #     account                 = self.get_account_balance()
    #     reg_list                = ['ETC', 'ETH', 'LTC', 'MLN', 'REP', 'XBT', 'XDG', 'XLM', 'XMR', 'XRP', 'ZEC']

    #     if self.has_result(account):
    #         account = account[Dicts.RESULT]
    #         for symbol, qty in account.items():
    #             qty = float(qty)
    #             if qty > 0 and symbol not in StableCoins.STABLE_COINS_LIST:
    #                 if symbol[-2:] == ".S":
    #                     continue
    #                 if symbol in reg_list:
    #                     symbol = "X" + symbol
                        
    #                 symbol_pair  = self.get_tradable_asset_pair(symbol)
    #                 qty_max_prec = self.get_max_volume_precision(symbol_pair)
    #                 qty          = self.round_decimals_down(qty, qty_max_prec)
    #                 result       = self.market_order(Trade.SELL, qty, symbol_pair)
                    
    #                 print("symbol",      symbol)
    #                 print("symbol_pair", symbol_pair)
    #                 print(symbol_pair,   result)
    #                 print()
    #     return

    # def __nuke_and_restart(self, sell: bool = False) -> None:
    #     sql = SQL()
    #     sql.drop_all_tables()
    #     sql.create_tables()
    #     self.cancel_all_orders()
        
    #     if sell:
    #         self.__sell_all_assets()
    #     return
    #----------------------------------------------------------------------------------------------------

    def get_elapsed_time(self, start_time: float) -> str:
        end_time     = time.time()
        elapsed_time = round(end_time - start_time)
        minutes      = elapsed_time // 60
        seconds      = elapsed_time % 60
        return f"{minutes} minutes {seconds} seconds"


##################################################################################################################################
### BUY_LOOP
##################################################################################################################################

    # def buy_loop(self) -> None:
    #     """The main function for trading coins."""
    #     self.__init_loop_variables()
        
    #     while True:
    #         start_time = time.time()
            
    #         for symbol in Buy_.SET:
    #             symbol_pair = self.get_tradable_asset_pair(symbol)
    #             self.wait(message=f"Checking {symbol}", timeout=Nap.NORMAL)
                
    #             self.__update_completed_trades(symbol_pair)
    #             self.__update_open_buy_orders(symbol_pair)
                
    #             if self.__is_buy(symbol):
    #                 self.__place_limit_orders(symbol, symbol_pair)
            
    #         G.log.print_and_log(message=Color.FG_BRIGHT_BLACK + f"Checked all coins in {self.get_elapsed_time(start_time)}" + Color.ENDC)
    #         print()
            
    #         self.wait(message=Color.FG_BRIGHT_BLACK + f"Waiting till {self.__get_buy_time()} to buy" + Color.ENDC, timeout=Buy_.TIME_MINUTES*60)
    #         G.log.print_and_log(message=Color.BG_GREEN + "Account Value          " + Color.ENDC + f" ${self.__get_account_value()}")
    #         G.log.print_and_log(message=Color.BG_GREEN + "Total Profit           " + Color.ENDC + f" ${self.round_decimals_down(self.total_profit, DECIMAL_MAX)}")
    #     return
